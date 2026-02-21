import type { AppLanguage } from './appSettings';

export type PendingReviewStatus = 'pending' | 'escalated';

export interface PendingReview {
  id: string;
  invoiceNumber: string;
  vendor: string;
  amount: string;
  date: string;
  status: PendingReviewStatus;
  contactEmail: string;
  reasons: Record<AppLanguage, string[]>;
  emailDraft: Record<AppLanguage, string>;
}

export const pendingReviews: PendingReview[] = [
  {
    id: 'review-1',
    invoiceNumber: 'INV-2391',
    vendor: 'TechSupply Inc',
    amount: '$12,450.00',
    date: '2026-02-19',
    status: 'pending',
    contactEmail: 'billing@techsupply.com',
    reasons: {
      fr: [
        'Le montant dépasse de 20% la moyenne de ce fournisseur sur les 6 derniers mois.',
        "Le bon de commande associé n'a pas été retrouvé dans le dossier de la période.",
      ],
      en: [
        "The amount is 20% above this vendor's average over the last 6 months.",
        'The related purchase order was not found in the period records.',
      ],
    },
    emailDraft: {
      fr: `Bonjour,\n\nNous avons bien reçu la facture INV-2391. Avant validation, nous avons besoin d'une clarification sur l'écart de montant constaté par rapport à vos dernières factures.\n\nPouvez-vous confirmer le périmètre exact des prestations facturées et partager le bon de commande correspondant ?\n\nMerci d'avance pour votre retour rapide.\n\nCordialement,\nÉquipe Accounts Payable`,
      en: `Hello,\n\nWe have received invoice INV-2391. Before validation, we need clarification regarding the amount variance identified compared with your recent invoices.\n\nCould you confirm the exact scope of billed services and share the corresponding purchase order?\n\nThank you in advance for your prompt response.\n\nBest regards,\nAccounts Payable Team`,
    },
  },
  {
    id: 'review-2',
    invoiceNumber: 'INV-2388',
    vendor: 'Cloud Services Ltd',
    amount: '$8,900.00',
    date: '2026-02-18',
    status: 'escalated',
    contactEmail: 'finance@cloudservices.io',
    reasons: {
      fr: ['Les coordonnées bancaires de la facture ne correspondent pas aux coordonnées habituelles du fournisseur.'],
      en: ['The bank details on this invoice do not match the vendor details on record.'],
    },
    emailDraft: {
      fr: `Bonjour,\n\nNous traitons actuellement la facture INV-2388. Une divergence a été détectée sur les informations bancaires fournies.\n\nMerci de confirmer officiellement les coordonnées de paiement à utiliser pour cette facture, ainsi que la personne de contact côté finance.\n\nDans l'attente de votre confirmation, nous gardons la facture en attente de validation.\n\nCordialement,\nÉquipe Accounts Payable`,
      en: `Hello,\n\nWe are currently processing invoice INV-2388. A discrepancy was detected in the banking details provided.\n\nPlease officially confirm the payment details to use for this invoice, along with the appropriate finance contact.\n\nUntil confirmation is received, we will keep the invoice pending validation.\n\nBest regards,\nAccounts Payable Team`,
    },
  },
  {
    id: 'review-3',
    invoiceNumber: 'INV-2379',
    vendor: 'Marketing Pro',
    amount: '$15,200.00',
    date: '2026-02-17',
    status: 'pending',
    contactEmail: 'accounts@marketingpro.com',
    reasons: {
      fr: [
        'Une facture proche (même montant et même période) a déjà été soumise récemment.',
        'Le descriptif des lignes est trop générique pour un contrôle comptable fiable.',
      ],
      en: [
        'A similar invoice (same amount and same period) was already submitted recently.',
        'Line-item descriptions are too generic for reliable accounting validation.',
      ],
    },
    emailDraft: {
      fr: `Bonjour,\n\nNous avons besoin d'une précision avant validation de la facture INV-2379. Une possible duplication a été détectée avec une facture récente sur la même période.\n\nMerci de confirmer si cette facture remplace un envoi précédent ou s'il s'agit d'une prestation différente, avec le détail des livrables associés.\n\nNous pourrons finaliser la validation dès réception de ces éléments.\n\nCordialement,\nÉquipe Accounts Payable`,
      en: `Hello,\n\nWe need clarification before validating invoice INV-2379. A possible duplicate was detected with a recent invoice for the same period.\n\nPlease confirm whether this invoice replaces a previous submission or covers a different service, and share the related deliverable details.\n\nWe can finalize validation as soon as we receive this information.\n\nBest regards,\nAccounts Payable Team`,
    },
  },
];
