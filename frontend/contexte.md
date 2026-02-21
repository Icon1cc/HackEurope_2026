# InvoiceGuard — Contexte Projet

> Ce fichier est la source de vérité pour toute IA travaillant sur ce projet.
> Il doit être mis à jour à chaque changement structurel significatif.
> Dernière mise à jour : 2026-02-21 (i18n FR/EN global + settings réduits à 4 champs + autosave des paramètres + tri colonnes au clic + suppression du bloc Processing/Pending Review/Escalated + section recherche/action de History alignée sur les proportions de Vendors)

---

## Vue d'ensemble

**InvoiceGuard** est une application web de traitement de factures par IA et de détection de fraude, destinée aux équipes de comptabilité fournisseur (Accounts Payable) des entreprises.

**Stack technique :**
- React 18 + TypeScript
- Vite 6 (bundler)
- React Router 7 (routing SPA)
- Tailwind CSS v4 (styling utilitaire)
- Radix UI (composants UI headless)
- MUI (icons + quelques composants)
- Recharts (graphiques)
- Sonner (notifications toast)
- Motion (animations)

---

## Structure du projet

```
InvoiceGuard Web App/
├── index.html                        # Entrée HTML (meta tags, OG)
├── package.json                      # name: "invoiceguard", v1.0.0
├── vite.config.ts                    # Build prod optimisé, port 3000
├── tsconfig.json                     # Config TypeScript (strict)
├── tsconfig.node.json                # Config TS pour vite.config
├── postcss.config.mjs
├── .gitignore
├── .env.example                      # Template variables d'environnement
├── contexte.md                       # CE FICHIER
├── guidelines/
└── src/
    ├── main.tsx                      # Entrée React (StrictMode)
    ├── styles/
    │   ├── index.css
    │   ├── fonts.css
    │   ├── tailwind.css
    │   └── theme.css                 # Design system CSS variables
    └── app/
        ├── App.tsx                   # RouterProvider + AppLanguageProvider
        ├── routes.ts                 # Toutes les routes
        ├── data/
        │   ├── mockVendors.ts        # Données mock partagées (vendors + factures)
        │   ├── pendingReviews.ts     # Données mock reviews (reasons/emailDraft FR+EN)
        │   └── appSettings.ts        # Schéma settings (4 champs) + persistance locale
        ├── i18n/
        │   └── AppLanguageProvider.tsx # Contexte langue global (FR/EN)
        ├── components/
        │   ├── Sidebar.tsx           # Navigation fixe gauche
        │   ├── Footer.tsx            # Copyright en bas de page
        │   ├── VercelBackground.tsx  # Fond avec texture grain
        │   └── ui/                   # ~60 wrappers Radix UI
        └── pages/
            ├── SignIn.tsx            # Page de connexion (/)
            ├── Dashboard.tsx         # Dashboard complet + panel pending reviews à droite
            ├── ReviewDetail.tsx      # Détail d'une review (/reviews/:reviewId)
            ├── Inbox.tsx             # Écran legacy non routé (référence UI historique)
            ├── Vendors.tsx           # Liste des vendors (/vendors)
            ├── VendorDetail.tsx      # Historique d'un vendor (/vendors/:vendorId)
            ├── History.tsx           # [CONSERVÉ mais non lié à la nav]
            └── Settings.tsx          # Paramètres applicatifs (/settings)
```

---

## Routes

| Path                    | Composant       | Statut      | Notes                              |
|-------------------------|-----------------|-------------|------------------------------------|
| `/`                     | SignIn          | Fonctionnel | Redirige vers /dashboard           |
| `/dashboard`            | Dashboard       | Fonctionnel | Dashboard + panel pending reviews à droite |
| `/reviews/:reviewId`    | ReviewDetail    | Fonctionnel | Page de review dédiée (preview + décision) |
| `/vendors`              | Vendors         | Fonctionnel | Liste + stats vendors              |
| `/vendors/:vendorId`    | VendorDetail    | Fonctionnel | Historique factures d'un vendor    |
| `/settings`             | Settings        | Fonctionnel | Profil + entreprise + langue (autosave) |

> La route `/inbox` a été supprimée. Les reviews sont listées dans `/dashboard` et ouvertes via `/reviews/:reviewId`.

---

## Navigation (Sidebar)

Items visibles dans le menu de gauche :
1. **Dashboard** — `/dashboard`
2. **Vendors** — `/vendors` (actif aussi sur `/vendors/:id`)

> **Inbox a été retiré de la nav** et fusionné dans Dashboard.  
> **History n'est pas dans la nav** (écran conservé mais non exposé par route active).
> **Bas de sidebar** : box utilisateur cliquable (nom + entreprise + email) avec menu d'actions (`Settings`, `Sign out`).
> Libellés de navigation et menu utilisateur traduits selon la langue préférée.

---

## Design System

**Thème** : Dark glassmorphic, défini dans `src/styles/theme.css`

| Token          | Valeur        | Usage                        |
|----------------|---------------|------------------------------|
| Background     | `#060709`     | Fond principal               |
| Card bg        | `rgba(20,22,25,0.6)` | Cartes / panneaux     |
| Foreground     | `#FAFAFA`     | Texte principal              |
| Muted          | `#71717A`     | Labels, texte secondaire     |
| Primary/Cyan   | `#00F2FF`     | Accent principal, liens actifs |
| Success/Green  | `#00FF94`     | Payé, fiable, hausse         |
| Warning/Amber  | `#FFB800`     | En attente, score C          |
| Danger/Red     | `#FF0055`     | Rejeté, risqué, baisse       |
| Purple         | `#A855F7`     | Accent secondaire            |

**Typographie** : Geist Sans, Inter — `fontWeight: 700`, `letterSpacing: -0.02em` pour les titres.

**Effets récurrents** :
- `backdrop-blur-[20px]` sur toutes les cartes
- `border: 1px solid rgba(255,255,255,0.1)` — bordure subtile
- `boxShadow: inset 0 1px 0 0 rgba(255,255,255,0.1)` — ligne lumineuse en haut
- `filter: drop-shadow(...)` pour les glows sur icônes et textes

---

## Données mock

### Vendors (`src/app/data/mockVendors.ts`)

Fichier centralisé partagé par `Vendors.tsx` et `VendorDetail.tsx`.

**Interface `Vendor`** :
```ts
{ id, name, category, trustScore: number (0–100), paid, pending, rejected, totalAmount, lastInvoice }
```
> `trustScore` est désormais uniquement numérique. Les champs `trustValue` (ancien alias) et `trend` ont été supprimés.

**Interface `VendorInvoice`** :
```ts
{ id, vendorId, date, invoiceNumber, amount, status: 'paid'|'pending'|'flagged'|'rejected' }
```

**15 vendors** avec IDs `'1'` à `'15'`, chacun ayant 4–5 factures mock.

### Pending Reviews (`src/app/data/pendingReviews.ts`)

Fichier centralisé partagé par `Dashboard.tsx` et `ReviewDetail.tsx`.

**Interface `PendingReview`** :
```ts
{
  id, invoiceNumber, vendor, amount, date, status, contactEmail,
  reasons: { fr: string[]; en: string[] },
  emailDraft: { fr: string; en: string }
}
```

**3 reviews mock** avec IDs `review-1` à `review-3`.

### App Settings (`src/app/data/appSettings.ts`)

- Type `AppSettings` limité à 4 champs :
  - `profileName`
  - `profileEmail`
  - `companyName`
  - `language` (`fr` | `en`)
- Valeurs par défaut centralisées dans `DEFAULT_APP_SETTINGS`
- Persistance locale via `loadAppSettings()` / `saveAppSettings()` sur `localStorage`

### i18n global (`src/app/i18n/AppLanguageProvider.tsx`)

- Fournit la langue active à toute l'app (`useAppLanguage`)
- Synchronise automatiquement via l'événement `invoiceguard:settings-updated`
- Met à jour `document.documentElement.lang`

### Trust Score → couleur (interpolation lisse)

`trustScore` est un entier **0–100**. La couleur est calculée via `getScoreColor(score)` (interpolation linéaire entre 4 stops) :

| Plage   | Couleur résultante         |
|---------|----------------------------|
| 0–50    | `#FF0055` → `#FFB800` (rouge → ambre) |
| 50–75   | `#FFB800` → `#00F2FF` (ambre → cyan)  |
| 75–100  | `#00F2FF` → `#00FF94` (cyan → vert)   |

**Affichage** : nombre coloré + barre de progression (3–4 px) avec un gradient CSS fixe `#FF0055 → #FFB800 → #00F2FF → #00FF94`, clippé à `width: score%`.

**Filtres numériques** :
- Très fiable : ≥ 80
- Bon : 60–79
- Moyen : 40–59
- À risque : < 40

---

## Pages détaillées

### Dashboard (`/dashboard`)
- **Métriques** : Valeur protégée ($2.4M), Heures économisées (342)
- **Line chart** : Volume de traitement (Recharts)
- **Zone upload** : Drag-and-drop de factures (mock)
- **Panel droite `Pending Reviews`** : liste cliquable (status, vendor, montant, raison courte)
- **Navigation review** : clic sur une review => route `/reviews/:reviewId`
- **Responsive** :
  - sidebar desktop uniquement (`lg+`)
  - menu mobile en **burger** ancré à gauche, ouvrant un panneau latéral gauche
  - layout empilé sur mobile (pending reviews en haut, contenu principal en dessous)
  - chart, paddings et tailles de texte ajustés pour petits écrans
- **i18n** : titres, sous-titres, labels panel et statuts pending/escalated traduits FR/EN

### ReviewDetail (`/reviews/:reviewId`)
- **Page dédiée par review** (une URL par facture en attente)
- **Preview document** au centre
- **Decision Panel** :
  - raisons de blocage uniquement (sans score IA)
  - destinataire email éditable
  - brouillon d'email de négociation pré-rempli, éditable (FR/EN selon langue)
  - actions `Approve Invoice` ou `Reject & Send Email`
- **i18n** : page entièrement localisée FR/EN (labels, feedbacks, statuts)

### Vendors (`/vendors`)
- **Tableau** : Vendor, Catégorie (masquée sur mobile), Trust Score, Payées, En cours, Rejetées, Montant total
- Cliquer sur une ligne → navigue vers `/vendors/:id`
- Recherche texte conservée
- Tri par colonne : clic en-tête => ascendant, 2e clic => descendant, 3e clic => aucun tri
- Pagination (10 par page)
- **Responsive** : sidebar burger mobile, marges et paddings adaptés.
- **i18n** : filtres, colonnes, empty state et pagination traduits FR/EN

### Inbox (`src/app/pages/Inbox.tsx`)
- Écran conservé dans le repo comme référence visuelle legacy
- **Non routé** : inaccessible depuis la navigation et les routes actives

### VendorDetail (`/vendors/:vendorId`)
- **Breadcrumb** : Vendors > Nom vendor
- **Carte vendor** : icône colorée, nom, catégorie, trust score
- **4 stats** : Total factures, Payées, En cours, Rejetées
- **Tableau factures** : Date, Facture #, Montant, Statut
- Recherche par numéro conservée
- Tri par colonne : clic en-tête => ascendant, 2e clic => descendant, 3e clic => aucun tri
- Pagination (8 par page)
- **Bloc supprimé** : indicateurs circulaires `Processing / Pending Review / Escalated` retirés
- **i18n** : breadcrumb, labels stats/table, statuts et pagination traduits FR/EN

### Settings (`/settings`)
- **Champs disponibles uniquement** :
  - nom complet
  - email
  - nom de l'entreprise
  - langue de préférence (fr/en)
- **Sauvegarde automatique** : chaque modification est persistée automatiquement (sans bouton Save)
- **Persistance locale** : sauvegarde `localStorage` via `src/app/data/appSettings.ts`

---

## État d'avancement

| Module            | Statut             |
|-------------------|--------------------|
| Dashboard         | Fonctionnel (mock) |
| ReviewDetail      | Fonctionnel (mock) |
| Inbox             | Legacy non routé   |
| Vendors           | Fonctionnel (mock) |
| VendorDetail      | Fonctionnel (mock) |
| Settings          | Fonctionnel (mock localStorage) |
| Auth (real)       | À faire            |
| API backend       | À faire            |
| History (général) | Conservé, non-nav/non-route |

---

## Scripts disponibles

```bash
npm run dev          # Dev server → http://localhost:3000 (auto-open)
npm run build        # Build production → dist/
npm run preview      # Preview du build → http://localhost:4173
npm run type-check   # Vérification TypeScript sans compilation
```

---

## Variables d'environnement

Voir `.env.example`. Variables exposées au bundle préfixées `VITE_`.

```
VITE_API_BASE_URL       # URL de l'API backend
VITE_API_VERSION        # Version API (ex: v1)
VITE_AUTH_PROVIDER      # Fournisseur auth
VITE_ENABLE_AI_CHAT     # Feature flag chat IA
VITE_ENABLE_VENDOR_MANAGEMENT  # Feature flag vendors
```

---

## Conventions de code

- **Typage strict** TypeScript — pas de `any`
- **Styles inline** via `style={{}}` pour les valeurs du design system (couleurs, glows)
- **Tailwind** pour layout, spacing, transitions
- **Gestionnaires d'événements** nommés (`handleXxx`) pour les actions non-triviales
- **Constantes** en SCREAMING_SNAKE pour les valeurs fixes (`ITEMS_PER_PAGE`)
- **Données mock** centralisées dans `src/app/data/` — ne pas dupliquer dans les pages
- **Pas de `History` dans la Sidebar** — navigation via vendors uniquement
