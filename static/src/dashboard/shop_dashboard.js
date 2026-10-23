import { Component, onWillStart, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { formatMonetary } from "@web/views/fields/formatters";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const { DateTime } = luxon;

const PALETTE = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#0ea5e9", "#8b5cf6", "#ef4444"];
const LOCAL_COLOR = PALETTE[0];
const ONLINE_COLOR = PALETTE[4];

export class ShopDashboard extends Component {
    static template = "script_shop_management.ShopDashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.periods = [
            { key: "today", label: _t("Today") },
            { key: "week", label: _t("This week") },
            { key: "month", label: _t("This month") },
            { key: "year", label: _t("This year") },
            { key: "custom", label: _t("Custom") },
        ];
        this.state = useState({
            shops: [],
            shop: null, // selected card, null while the cards are displayed
            period: "month",
            dateFrom: "",
            dateTo: "",
            data: null,
            loading: false,
        });
        this.timelineRef = useRef("timelineChart");
        this.shareRef = useRef("shareChart");
        this.topRef = useRef("topChart");
        this.channelRef = useRef("channelChart");
        this.charts = [];

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            this.state.shops = await this.orm.call("shop.dashboard", "get_shops", []);
        });
        useEffect(
            () => {
                this.renderCharts();
            },
            () => [this.state.data]
        );
        onWillUnmount(() => this.destroyCharts());
    }

    // ------------------------------------------------------------------ navigation

    async openShop(shop) {
        this.state.shop = shop;
        await this.selectPeriod(this.state.period);
    }

    backToShops() {
        this.destroyCharts();
        this.state.shop = null;
        this.state.data = null;
    }

    async selectPeriod(key) {
        this.state.period = key;
        const today = DateTime.local().startOf("day");
        const ranges = {
            today: [today, today],
            week: [today.startOf("week"), today.endOf("week").startOf("day")],
            month: [today.startOf("month"), today.endOf("month").startOf("day")],
            year: [today.startOf("year"), today.endOf("year").startOf("day")],
        };
        if (ranges[key]) {
            this.state.dateFrom = ranges[key][0].toISODate();
            this.state.dateTo = ranges[key][1].toISODate();
        }
        if (key !== "custom" || (this.state.dateFrom && this.state.dateTo)) {
            await this.loadData();
        }
    }

    async onDateChange(field, ev) {
        this.state[field] = ev.target.value;
        this.state.period = "custom";
        if (this.state.dateFrom && this.state.dateTo) {
            await this.loadData();
        }
    }

    async loadData() {
        this.state.loading = true;
        try {
            this.state.data = await this.orm.call("shop.dashboard", "get_data", [
                this.state.shop.id,
                this.state.dateFrom,
                this.state.dateTo,
                this.state.shop.website_id,
            ]);
        } finally {
            this.state.loading = false;
        }
    }

    money(value) {
        return formatMonetary(value, { currencyId: this.state.data.currency_id });
    }

    /** The "all shops" card: no single shop nor online shop selected. */
    get isAllShops() {
        return !this.state.shop.id && !this.state.shop.website_id;
    }

    /** The online figures are shown for the all shops card and for every shop with an online shop. */
    get showOnline() {
        return this.isAllShops || this.state.shop.online;
    }

    get shareTitle() {
        return this.isAllShops ? _t("Turnover by shop") : _t("Best sellers share");
    }

    /** Open the matching list of the module, filtered on the selected shop. */
    openList(xmlid, searchField) {
        const shop = this.state.shop;
        if (shop.website_id) {
            return; // the lists are filtered on the local shops, not on an online shop
        }
        this.actionService.doAction(`script_shop_management.${xmlid}`, {
            additionalContext: shop.id ? { [`search_default_${searchField}`]: shop.id } : {},
        });
    }

    // ---------------------------------------------------------------------- charts

    destroyCharts() {
        for (const chart of this.charts) {
            chart.destroy();
        }
        this.charts = [];
    }

    lineDataset(label, values, color, background) {
        return {
            label,
            data: values,
            borderColor: color,
            backgroundColor: background,
            fill: true,
            tension: 0.4,
            borderWidth: 3,
            pointRadius: 0,
            pointHoverRadius: 6,
        };
    }

    renderCharts() {
        this.destroyCharts();
        const data = this.state.data;
        if (!data || !this.timelineRef.el || !window.Chart) {
            return;
        }
        const textColor = getComputedStyle(document.body).color || "#374151";
        const gridColor = "rgba(128, 128, 128, 0.15)";
        Chart.defaults.color = textColor;
        Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
        const money = (value) => this.money(value);

        // Sales vs purchases: smooth area curves
        const ctx = this.timelineRef.el.getContext("2d");
        const gradient = (color) => {
            const g = ctx.createLinearGradient(0, 0, 0, 300);
            g.addColorStop(0, color + "66");
            g.addColorStop(1, color + "00");
            return g;
        };
        this.charts.push(
            new Chart(this.timelineRef.el, {
                type: "line",
                data: {
                    labels: data.timeline.labels,
                    datasets: [
                        this.lineDataset(_t("Local turnover"), data.timeline.sales, LOCAL_COLOR, gradient(LOCAL_COLOR)),
                        ...(this.showOnline
                            ? [this.lineDataset(_t("Online turnover"), data.timeline.online, ONLINE_COLOR, gradient(ONLINE_COLOR))]
                            : []),
                        this.lineDataset(_t("Purchases"), data.timeline.purchases, PALETTE[2], gradient(PALETTE[2])),
                    ],
                },
                options: {
                    maintainAspectRatio: false,
                    interaction: { mode: "index", intersect: false },
                    plugins: {
                        legend: { position: "top", align: "end", labels: { usePointStyle: true } },
                        tooltip: {
                            callbacks: {
                                label: (item) => `${item.dataset.label}: ${money(item.parsed.y)}`,
                            },
                        },
                    },
                    scales: {
                        x: { grid: { display: false } },
                        y: { beginAtZero: true, grid: { color: gridColor }, border: { display: false } },
                    },
                },
            })
        );

        // Doughnut: turnover by shop (all shops) or share of the best sellers (one shop)
        const shareItems = this.isAllShops
            ? data.by_shop.map((s) => ({ name: s.name, value: s.amount }))
            : data.top_products.map((p) => ({ name: p.name, value: p.qty }));
        this.charts.push(
            new Chart(this.shareRef.el, {
                type: "doughnut",
                data: {
                    labels: shareItems.map((i) => i.name),
                    datasets: [
                        {
                            data: shareItems.map((i) => i.value),
                            backgroundColor: PALETTE,
                            borderWidth: 0,
                            hoverOffset: 8,
                        },
                    ],
                },
                options: {
                    maintainAspectRatio: false,
                    cutout: "68%",
                    plugins: {
                        legend: { position: "bottom", labels: { usePointStyle: true } },
                        tooltip: {
                            callbacks: {
                                label: (item) =>
                                    this.isAllShops
                                        ? `${item.label}: ${money(item.parsed)}`
                                        : `${item.label}: ${item.parsed}`,
                            },
                        },
                    },
                },
            })
        );

        // Online against local: share of the real turnover
        if (this.channelRef.el) {
            this.charts.push(
                new Chart(this.channelRef.el, {
                    type: "doughnut",
                    data: {
                        labels: [_t("Local"), _t("Online")],
                        datasets: [
                            {
                                data: [
                                    data.channels.local.real_revenue,
                                    data.channels.online.real_revenue,
                                ],
                                backgroundColor: [LOCAL_COLOR, ONLINE_COLOR],
                                borderWidth: 0,
                                hoverOffset: 8,
                            },
                        ],
                    },
                    options: {
                        maintainAspectRatio: false,
                        cutout: "68%",
                        plugins: {
                            legend: { position: "bottom", labels: { usePointStyle: true } },
                            tooltip: {
                                callbacks: { label: (item) => `${item.label}: ${money(item.parsed)}` },
                            },
                        },
                    },
                })
            );
        }

        // Best sellers: rounded horizontal bars
        this.charts.push(
            new Chart(this.topRef.el, {
                type: "bar",
                data: {
                    labels: data.top_products.map((p) => p.name),
                    datasets: [
                        {
                            data: data.top_products.map((p) => p.qty),
                            backgroundColor: PALETTE[1],
                            borderRadius: 8,
                            borderSkipped: false,
                            barThickness: 18,
                        },
                    ],
                },
                options: {
                    indexAxis: "y",
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { beginAtZero: true, grid: { color: gridColor }, border: { display: false } },
                        y: { grid: { display: false } },
                    },
                },
            })
        );
    }
}

registry.category("actions").add("script_shop_management.dashboard", ShopDashboard);
