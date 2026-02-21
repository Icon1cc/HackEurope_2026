export interface Vendor {
  id: string;
  name: string;
  category: string;
  trustScore: number; // 0–100
  paid: number;
  pending: number;
  rejected: number;
  totalAmount: string;
  lastInvoice: string;
}

export interface VendorInvoice {
  id: string;
  vendorId: string;
  date: string;
  invoiceNumber: string;
  amount: string;
  status: 'paid' | 'pending' | 'flagged' | 'rejected';
}

export const mockVendors: Vendor[] = [
  { id: '1',  name: 'Acme Corp',             category: 'Technology',      trustScore: 98, paid: 42, pending: 1, rejected: 0, totalAmount: '$248,500', lastInvoice: '2026-02-20' },
  { id: '2',  name: 'Legal Advisors LLP',     category: 'Legal',           trustScore: 97, paid: 28, pending: 0, rejected: 0, totalAmount: '$420,000', lastInvoice: '2026-02-17' },
  { id: '3',  name: 'Cloud Services Ltd',     category: 'Infrastructure',  trustScore: 91, paid: 36, pending: 2, rejected: 1, totalAmount: '$115,200', lastInvoice: '2026-02-18' },
  { id: '4',  name: 'IT Solutions Inc',       category: 'Technology',      trustScore: 88, paid: 19, pending: 3, rejected: 1, totalAmount: '$180,500', lastInvoice: '2026-02-16' },
  { id: '5',  name: 'Marketing Pro Agency',   category: 'Marketing',       trustScore: 84, paid: 15, pending: 2, rejected: 2, totalAmount: '$118,350', lastInvoice: '2026-02-18' },
  { id: '6',  name: 'Office Depot',           category: 'Supplies',        trustScore: 90, paid: 61, pending: 1, rejected: 0, totalAmount: '$53,780',  lastInvoice: '2026-02-19' },
  { id: '7',  name: 'TechSupply Inc',         category: 'Hardware',        trustScore: 72, paid: 9,  pending: 4, rejected: 3, totalAmount: '$97,400',  lastInvoice: '2026-02-19' },
  { id: '8',  name: 'Shipping Express',       category: 'Logistics',       trustScore: 45, paid: 7,  pending: 2, rejected: 5, totalAmount: '$21,250',  lastInvoice: '2026-02-17' },
  { id: '9',  name: 'DataStream Analytics',   category: 'Software',        trustScore: 93, paid: 24, pending: 1, rejected: 0, totalAmount: '$204,000', lastInvoice: '2026-02-15' },
  { id: '10', name: 'HR Connect',             category: 'Human Resources', trustScore: 79, paid: 12, pending: 3, rejected: 2, totalAmount: '$66,800',  lastInvoice: '2026-02-14' },
  { id: '11', name: 'SecureNet Systems',      category: 'Cybersecurity',   trustScore: 99, paid: 18, pending: 0, rejected: 0, totalAmount: '$312,000', lastInvoice: '2026-02-12' },
  { id: '12', name: 'FastPrint Co.',          category: 'Printing',        trustScore: 55, paid: 5,  pending: 1, rejected: 4, totalAmount: '$14,300',  lastInvoice: '2026-02-10' },
  { id: '13', name: 'GlobalTrade Partners',   category: 'Import/Export',   trustScore: 31, paid: 3,  pending: 5, rejected: 6, totalAmount: '$78,900',  lastInvoice: '2026-02-08' },
  { id: '14', name: 'FinServ Consulting',     category: 'Finance',         trustScore: 89, paid: 22, pending: 1, rejected: 1, totalAmount: '$390,500', lastInvoice: '2026-02-20' },
  { id: '15', name: 'MediaHouse Studios',     category: 'Media',           trustScore: 76, paid: 8,  pending: 2, rejected: 1, totalAmount: '$44,200',  lastInvoice: '2026-02-06' },
];

export const mockVendorInvoices: VendorInvoice[] = [
  // Acme Corp (1)
  { id: 'i01', vendorId: '1', date: '2026-02-20', invoiceNumber: 'INV-2345', amount: '$5,234.00',  status: 'paid'    },
  { id: 'i02', vendorId: '1', date: '2026-02-10', invoiceNumber: 'INV-2301', amount: '$6,100.00',  status: 'paid'    },
  { id: 'i03', vendorId: '1', date: '2026-01-28', invoiceNumber: 'INV-2280', amount: '$4,900.50',  status: 'paid'    },
  { id: 'i04', vendorId: '1', date: '2026-01-15', invoiceNumber: 'INV-2250', amount: '$5,500.00',  status: 'pending' },
  { id: 'i05', vendorId: '1', date: '2026-01-05', invoiceNumber: 'INV-2220', amount: '$5,800.00',  status: 'paid'    },

  // Legal Advisors LLP (2)
  { id: 'i06', vendorId: '2', date: '2026-02-17', invoiceNumber: 'INV-2339', amount: '$15,000.00', status: 'paid'    },
  { id: 'i07', vendorId: '2', date: '2026-02-01', invoiceNumber: 'INV-2295', amount: '$15,000.00', status: 'paid'    },
  { id: 'i08', vendorId: '2', date: '2026-01-15', invoiceNumber: 'INV-2255', amount: '$15,000.00', status: 'paid'    },
  { id: 'i09', vendorId: '2', date: '2026-01-02', invoiceNumber: 'INV-2210', amount: '$15,000.00', status: 'paid'    },

  // Cloud Services Ltd (3)
  { id: 'i10', vendorId: '3', date: '2026-02-18', invoiceNumber: 'INV-2342', amount: '$3,200.00',  status: 'pending' },
  { id: 'i11', vendorId: '3', date: '2026-02-05', invoiceNumber: 'INV-2298', amount: '$3,200.00',  status: 'paid'    },
  { id: 'i12', vendorId: '3', date: '2026-01-20', invoiceNumber: 'INV-2265', amount: '$3,200.00',  status: 'paid'    },
  { id: 'i13', vendorId: '3', date: '2026-01-05', invoiceNumber: 'INV-2215', amount: '$3,450.00',  status: 'rejected'},
  { id: 'i14', vendorId: '3', date: '2025-12-22', invoiceNumber: 'INV-2180', amount: '$3,200.00',  status: 'paid'    },

  // IT Solutions Inc (4)
  { id: 'i15', vendorId: '4', date: '2026-02-16', invoiceNumber: 'INV-2338', amount: '$9,500.00',  status: 'pending' },
  { id: 'i16', vendorId: '4', date: '2026-02-03', invoiceNumber: 'INV-2296', amount: '$9,200.00',  status: 'paid'    },
  { id: 'i17', vendorId: '4', date: '2026-01-18', invoiceNumber: 'INV-2260', amount: '$9,800.00',  status: 'pending' },
  { id: 'i18', vendorId: '4', date: '2026-01-04', invoiceNumber: 'INV-2218', amount: '$9,500.00',  status: 'paid'    },
  { id: 'i19', vendorId: '4', date: '2025-12-20', invoiceNumber: 'INV-2177', amount: '$10,500.00', status: 'rejected'},

  // Marketing Pro Agency (5)
  { id: 'i20', vendorId: '5', date: '2026-02-18', invoiceNumber: 'INV-2341', amount: '$7,890.00',  status: 'paid'    },
  { id: 'i21', vendorId: '5', date: '2026-02-04', invoiceNumber: 'INV-2297', amount: '$7,890.00',  status: 'pending' },
  { id: 'i22', vendorId: '5', date: '2026-01-20', invoiceNumber: 'INV-2262', amount: '$8,100.00',  status: 'paid'    },
  { id: 'i23', vendorId: '5', date: '2026-01-06', invoiceNumber: 'INV-2222', amount: '$7,500.00',  status: 'rejected'},
  { id: 'i24', vendorId: '5', date: '2025-12-15', invoiceNumber: 'INV-2170', amount: '$7,890.00',  status: 'paid'    },

  // Office Depot (6)
  { id: 'i25', vendorId: '6', date: '2026-02-19', invoiceNumber: 'INV-2343', amount: '$892.50',    status: 'paid'    },
  { id: 'i26', vendorId: '6', date: '2026-02-12', invoiceNumber: 'INV-2310', amount: '$745.00',    status: 'paid'    },
  { id: 'i27', vendorId: '6', date: '2026-02-05', invoiceNumber: 'INV-2299', amount: '$1,020.00',  status: 'pending' },
  { id: 'i28', vendorId: '6', date: '2026-01-28', invoiceNumber: 'INV-2282', amount: '$880.00',    status: 'paid'    },
  { id: 'i29', vendorId: '6', date: '2026-01-21', invoiceNumber: 'INV-2268', amount: '$650.00',    status: 'paid'    },

  // TechSupply Inc (7)
  { id: 'i30', vendorId: '7', date: '2026-02-19', invoiceNumber: 'INV-2344', amount: '$12,450.00', status: 'flagged' },
  { id: 'i31', vendorId: '7', date: '2026-02-08', invoiceNumber: 'INV-2305', amount: '$11,200.00', status: 'pending' },
  { id: 'i32', vendorId: '7', date: '2026-01-25', invoiceNumber: 'INV-2275', amount: '$13,000.00', status: 'rejected'},
  { id: 'i33', vendorId: '7', date: '2026-01-10', invoiceNumber: 'INV-2240', amount: '$12,450.00', status: 'paid'    },
  { id: 'i34', vendorId: '7', date: '2025-12-28', invoiceNumber: 'INV-2195', amount: '$12,450.00', status: 'paid'    },

  // Shipping Express (8)
  { id: 'i35', vendorId: '8', date: '2026-02-17', invoiceNumber: 'INV-2340', amount: '$425.00',    status: 'rejected'},
  { id: 'i36', vendorId: '8', date: '2026-02-07', invoiceNumber: 'INV-2302', amount: '$425.00',    status: 'flagged' },
  { id: 'i37', vendorId: '8', date: '2026-01-24', invoiceNumber: 'INV-2272', amount: '$510.00',    status: 'rejected'},
  { id: 'i38', vendorId: '8', date: '2026-01-10', invoiceNumber: 'INV-2242', amount: '$425.00',    status: 'paid'    },
  { id: 'i39', vendorId: '8', date: '2025-12-30', invoiceNumber: 'INV-2200', amount: '$400.00',    status: 'paid'    },

  // DataStream Analytics (9)
  { id: 'i40', vendorId: '9', date: '2026-02-15', invoiceNumber: 'INV-2335', amount: '$8,500.00',  status: 'paid'    },
  { id: 'i41', vendorId: '9', date: '2026-02-01', invoiceNumber: 'INV-2290', amount: '$8,500.00',  status: 'paid'    },
  { id: 'i42', vendorId: '9', date: '2026-01-15', invoiceNumber: 'INV-2252', amount: '$8,500.00',  status: 'pending' },
  { id: 'i43', vendorId: '9', date: '2026-01-01', invoiceNumber: 'INV-2208', amount: '$8,500.00',  status: 'paid'    },

  // HR Connect (10)
  { id: 'i44', vendorId: '10', date: '2026-02-14', invoiceNumber: 'INV-2332', amount: '$5,567.00', status: 'paid'    },
  { id: 'i45', vendorId: '10', date: '2026-02-02', invoiceNumber: 'INV-2293', amount: '$5,567.00', status: 'pending' },
  { id: 'i46', vendorId: '10', date: '2026-01-18', invoiceNumber: 'INV-2258', amount: '$5,800.00', status: 'rejected'},
  { id: 'i47', vendorId: '10', date: '2026-01-03', invoiceNumber: 'INV-2211', amount: '$5,567.00', status: 'paid'    },
  { id: 'i48', vendorId: '10', date: '2025-12-20', invoiceNumber: 'INV-2178', amount: '$5,000.00', status: 'pending' },

  // SecureNet Systems (11)
  { id: 'i49', vendorId: '11', date: '2026-02-12', invoiceNumber: 'INV-2325', amount: '$17,333.00', status: 'paid'   },
  { id: 'i50', vendorId: '11', date: '2026-01-28', invoiceNumber: 'INV-2284', amount: '$17,333.00', status: 'paid'   },
  { id: 'i51', vendorId: '11', date: '2026-01-14', invoiceNumber: 'INV-2248', amount: '$17,333.00', status: 'paid'   },
  { id: 'i52', vendorId: '11', date: '2026-01-01', invoiceNumber: 'INV-2205', amount: '$17,333.00', status: 'paid'   },

  // FastPrint Co. (12)
  { id: 'i53', vendorId: '12', date: '2026-02-10', invoiceNumber: 'INV-2318', amount: '$2,860.00',  status: 'pending'},
  { id: 'i54', vendorId: '12', date: '2026-01-26', invoiceNumber: 'INV-2278', amount: '$2,860.00',  status: 'rejected'},
  { id: 'i55', vendorId: '12', date: '2026-01-12', invoiceNumber: 'INV-2244', amount: '$3,100.00',  status: 'rejected'},
  { id: 'i56', vendorId: '12', date: '2025-12-28', invoiceNumber: 'INV-2193', amount: '$2,860.00',  status: 'paid'   },
  { id: 'i57', vendorId: '12', date: '2025-12-14', invoiceNumber: 'INV-2160', amount: '$2,860.00',  status: 'paid'   },

  // GlobalTrade Partners (13)
  { id: 'i58', vendorId: '13', date: '2026-02-08', invoiceNumber: 'INV-2312', amount: '$11,271.00', status: 'rejected'},
  { id: 'i59', vendorId: '13', date: '2026-01-25', invoiceNumber: 'INV-2274', amount: '$11,271.00', status: 'flagged' },
  { id: 'i60', vendorId: '13', date: '2026-01-11', invoiceNumber: 'INV-2241', amount: '$12,900.00', status: 'rejected'},
  { id: 'i61', vendorId: '13', date: '2025-12-27', invoiceNumber: 'INV-2192', amount: '$11,271.00', status: 'pending' },
  { id: 'i62', vendorId: '13', date: '2025-12-13', invoiceNumber: 'INV-2158', amount: '$11,271.00', status: 'paid'   },

  // FinServ Consulting (14)
  { id: 'i63', vendorId: '14', date: '2026-02-20', invoiceNumber: 'INV-2346', amount: '$17,750.00', status: 'paid'   },
  { id: 'i64', vendorId: '14', date: '2026-02-06', invoiceNumber: 'INV-2300', amount: '$17,750.00', status: 'pending'},
  { id: 'i65', vendorId: '14', date: '2026-01-23', invoiceNumber: 'INV-2270', amount: '$18,000.00', status: 'paid'   },
  { id: 'i66', vendorId: '14', date: '2026-01-09', invoiceNumber: 'INV-2235', amount: '$17,750.00', status: 'paid'   },
  { id: 'i67', vendorId: '14', date: '2025-12-26', invoiceNumber: 'INV-2190', amount: '$19,000.00', status: 'rejected'},

  // MediaHouse Studios (15)
  { id: 'i68', vendorId: '15', date: '2026-02-06', invoiceNumber: 'INV-2308', amount: '$5,525.00',  status: 'paid'   },
  { id: 'i69', vendorId: '15', date: '2026-01-23', invoiceNumber: 'INV-2271', amount: '$5,525.00',  status: 'pending'},
  { id: 'i70', vendorId: '15', date: '2026-01-09', invoiceNumber: 'INV-2236', amount: '$5,800.00',  status: 'paid'   },
  { id: 'i71', vendorId: '15', date: '2025-12-26', invoiceNumber: 'INV-2191', amount: '$5,525.00',  status: 'rejected'},
  { id: 'i72', vendorId: '15', date: '2025-12-12', invoiceNumber: 'INV-2157', amount: '$5,525.00',  status: 'paid'   },
];
