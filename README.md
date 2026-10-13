<p align="center">
  <img src="static/description/icon.png" alt="Script Shop Management" width="140">
</p>

<h1 align="center">Script Shop Management</h1>

<p align="center">
  <b>Pilotez toutes vos boutiques physiques depuis une seule application Odoo 19.</b><br>
  Achats, ventes en caisse, stock et chiffre d'affaires, boutique par boutique.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Odoo-19.0-714B67" alt="Odoo 19">
  <img src="https://img.shields.io/badge/licence-LGPL--3-blue" alt="LGPL-3">
  <img src="https://img.shields.io/badge/éditeur-Script%20Consulting-0d9488" alt="Script Consulting">
</p>

---

## À quoi sert ce module ?

Quand une entreprise possède plusieurs boutiques, les informations sont dispersées dans Odoo : les ventes dans le Point de Vente, les achats dans Achats, les mouvements dans Inventaire. Il est difficile de répondre simplement à la question **« comment se porte ma boutique ? »**.

**Script Shop Management** rassemble ces informations dans une application unique. Chaque boutique est un point de vente Odoo, et le module relie à cette boutique les achats, les ventes, le stock et les produits qui la concernent. Le gérant voit en un coup d'œil l'activité de chaque boutique, ou de toutes les boutiques réunies.

## Ce que le module permet de faire

### 🏬 Déclarer ses boutiques
Dans la configuration d'un point de vente, une simple case **« Est une boutique »** le transforme en boutique, avec sa propre **image**. Les autres points de vente (stands, événements, ventes en ligne) restent en dehors du suivi.

### 📦 Savoir où chaque produit est vendu
Sur la fiche produit, le champ **« Disponible dans les boutiques »** indique dans quelles boutiques le produit est proposé. On sait immédiatement ce que chaque boutique a en rayon.

### 🛒 Rattacher les achats à une boutique
Chaque bon de commande fournisseur peut recevoir une **« Boutique de destination »**. On suit ainsi ce qui est acheté pour chaque boutique, et combien cela coûte.

### 🚚 Suivre les transferts de stock
Les transferts d'inventaire portent aussi une **« Boutique de destination »**. Les réapprovisionnements de chaque boutique sont visibles et traçables.

### 📊 Un tableau de bord par boutique
L'écran d'accueil affiche une carte **« Toutes les boutiques »** (avec le logo de la société) et une carte par boutique (avec son image). Un clic ouvre le tableau de bord de la boutique, avec un **sélecteur de période** et les indicateurs clés :

- montant des **achats** ;
- montant des **ventes** ;
- état du **stock** ;
- **chiffre d'affaires réel** ;
- **produits les plus vendus** et **les moins vendus**.

### 🔎 Des listes dédiées et une recherche rapide
Trois menus regroupent l'activité des boutiques, sans le bruit du reste d'Odoo :

| Menu | Contenu |
|---|---|
| **Achats** | Les achats ayant une boutique de destination |
| **Commandes** | Les commandes de caisse passées dans une boutique |
| **Stock** | Les transferts destinés à une boutique |

Dans chacun, la recherche se fait **par boutique** et **par produit**.

### 🔐 Des accès adaptés à chaque rôle
- **Utilisateur** : consulte l'activité des boutiques.
- **Responsable** : configure les boutiques et dispose de tous les droits.

Le module respecte le **multi-société** : chaque société ne voit que ses propres boutiques.

## Pour qui ?

- Les commerçants qui gèrent **plusieurs boutiques** avec Odoo Point de Vente.
- Les gérants qui veulent **comparer leurs boutiques** et repérer les produits qui marchent.
- Les intégrateurs Odoo qui cherchent une base simple et claire pour un réseau de magasins.

## Prérequis

- **Odoo 19.0** (Community ou Enterprise)
- Modules **Point de Vente**, **Achats** et **Inventaire** (installés automatiquement)

## Installation

1. Cloner le dépôt dans un dossier d'addons d'Odoo, **sous le nom `script_shop_management`** :
   ```bash
   git clone https://github.com/MaxTemat/Script_Shop_Management.git script_shop_management
   ```
2. Redémarrer Odoo, activer le mode développeur, puis **Applications → Mettre à jour la liste des applications**.
3. Rechercher **Script Shop Management** et cliquer sur **Activer**.

## Auteur

Développé par **Script Consulting**, consultant IT Odoo, dans le cadre de la série vidéo **« Boutique Locale »**.

## Licence

Distribué sous licence [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html).
