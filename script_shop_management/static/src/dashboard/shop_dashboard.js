import { Component, onWillStart, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { formatMonetary } from "@web/views/fields/formatters";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const { DateTime } = luxon;

const PALETTE = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#0ea5e9", "#8b5cf6", "#ef4444"];

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
            ]);
        } finally {
            this.state.loading = false;
        }
    }

    money(value) {
        return formatMonetary(value, { currencyId: this.state.data.currency_id });
    }

    get shareTitle() {
        return this.state.shop.id ? _t("Best sellers share") : _t("Turnover by shop");
    }

    /** Open the matching list of the module, filtered on the selected shop. */
    openList(xmlid, searchField) {
        const shop = this.state.shop;
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
                        {
                            label: _t("Real turnover"),
                            data: data.timeline.sales,
                            borderColor: PALETTE[0],
                            backgroundColor: gradient(PALETTE[0]),
                            fill: true,
                            tension: 0.4,
                            borderWidth: 3,
                            pointRadius: 0,
                            pointHoverRadius: 6,
                        },
                        {
                            label: _t("Purchases"),
                            data: data.timeline.purchases,
                            borderColor: PALETTE[2],
                            backgroundColor: gradient(PALETTE[2]),
                            fill: true,
                            tension: 0.4,
                            borderWidth: 3,
                            pointRadius: 0,
                            pointHoverRadius: 6,
                        },
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
        const shareItems = this.state.shop.id
            ? data.top_products.map((p) => ({ name: p.name, value: p.qty }))
            : data.by_shop.map((s) => ({ name: s.name, value: s.amount }));
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
                                    this.state.shop.id
                                        ? `${item.label}: ${item.parsed}`
                                        : `${item.label}: ${money(item.parsed)}`,
                            },
                        },
                    },
                },
            })
        );

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
