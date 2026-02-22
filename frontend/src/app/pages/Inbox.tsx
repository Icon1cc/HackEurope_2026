import { useState } from 'react';
import { Sidebar } from '../components/Sidebar';
import { VercelBackground } from '../components/VercelBackground';
import { AlertTriangle, FileText, CheckCircle2, XCircle, AlertCircle, Send, Brain, TrendingUp, Shield } from 'lucide-react';

interface InboxItem {
  id: string;
  vendor: string;
  amount: string;
  date: string;
  status: 'flagged' | 'escalated';
  reason: string;
  confidence: number;
}

const inboxItems: InboxItem[] = [
  { 
    id: '1', 
    vendor: 'TechSupply Inc', 
    amount: '$12,450.00', 
    date: '2026-02-19', 
    status: 'flagged',
    reason: 'Amount 20% higher than average',
    confidence: 85
  },
  { 
    id: '2', 
    vendor: 'PlatformOps AG', 
    amount: '$8,900.00', 
    date: '2026-02-18', 
    status: 'escalated',
    reason: 'Bank details mismatch detected',
    confidence: 45
  },
  { 
    id: '3', 
    vendor: 'Marketing Pro', 
    amount: '$15,200.00', 
    date: '2026-02-17', 
    status: 'flagged',
    reason: 'Duplicate invoice suspected',
    confidence: 72
  },
];

export default function Inbox() {
  const [selectedInvoice, setSelectedInvoice] = useState(inboxItems[0]);
  const [chatMessage, setChatMessage] = useState('');

  return (
    <div className="flex min-h-screen relative overflow-hidden">
      <VercelBackground />

      <Sidebar />
      
      <main className="flex-1 ml-64 flex relative z-10">
        {/* Left Panel - Inbox List */}
        <div 
          className="w-[380px] p-6 overflow-y-auto border-r backdrop-blur-[20px]"
          style={{
            background: 'rgba(6, 7, 9, 0.6)',
            borderColor: 'rgba(255, 255, 255, 0.1)',
          }}
        >
          <div className="mb-6">
            <h1 
              className="text-2xl mb-1"
              style={{ 
                fontFamily: 'Geist Sans, Inter, sans-serif',
                fontWeight: 700,
                letterSpacing: '-0.02em',
              }}
            >
              Pending Review
            </h1>
            <p className="text-[#71717A] text-sm">{inboxItems.length} invoices flagged by AI</p>
          </div>

          <div className="space-y-3">
            {inboxItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setSelectedInvoice(item)}
                className="w-full text-left p-4 rounded-lg transition-all duration-200"
                style={selectedInvoice.id === item.id ? {
                  background: 'rgba(0, 242, 255, 0.08)',
                  border: '1px solid rgba(0, 242, 255, 0.2)',
                  boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
                } : {
                  background: 'rgba(20, 22, 25, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
                onMouseEnter={(e) => {
                  if (selectedInvoice.id !== item.id) {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedInvoice.id !== item.id) {
                    e.currentTarget.style.background = 'rgba(20, 22, 25, 0.6)';
                  }
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {item.status === 'flagged' ? (
                      <AlertTriangle className="w-4 h-4 text-[#FFB800]" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-[#FF0055]" />
                    )}
                    {/* Badge with colored text and border on dark neutral background */}
                    <span 
                      className="text-xs px-2 py-0.5 rounded uppercase tracking-wider font-semibold"
                      style={item.status === 'flagged' ? {
                        background: 'rgba(20, 22, 25, 0.8)',
                        color: '#FFB800',
                        border: '1px solid #FFB800',
                      } : {
                        background: 'rgba(20, 22, 25, 0.8)',
                        color: '#FF0055',
                        border: '1px solid #FF0055',
                      }}
                    >
                      {item.status}
                    </span>
                  </div>
                  <div className="text-xs text-[#71717A]">{item.date}</div>
                </div>
                
                <div className="text-[#FAFAFA] font-semibold mb-1 text-sm">{item.vendor}</div>
                <div className="text-[#00F2FF] text-lg font-bold display-number mb-2">{item.amount}</div>
                <div className="text-xs text-[#71717A]">{item.reason}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Right Panel - Split View */}
        <div className="flex-1 flex">
          {/* PDF Preview */}
          <div className="flex-1 p-8 overflow-y-auto">
            <div className="mb-6">
              <h2 
                className="text-2xl mb-1"
                style={{ 
                  fontFamily: 'Geist Sans, Inter, sans-serif',
                  fontWeight: 700,
                  letterSpacing: '-0.02em',
                }}
              >
                Invoice Document
              </h2>
              <p className="text-[#71717A] text-sm">
                {selectedInvoice.vendor} • {selectedInvoice.id.padStart(7, 'INV-000')}
              </p>
            </div>

            {/* Mock PDF Viewer */}
            <div 
              className="rounded-xl p-8 backdrop-blur-[20px]"
              style={{
                background: 'rgba(20, 22, 25, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
              }}
            >
              <div className="max-w-2xl mx-auto bg-white rounded-lg p-12 text-left shadow-2xl">
                <div className="border-b border-gray-300 pb-6 mb-6">
                  <div className="text-3xl text-gray-900 mb-2 font-bold">{selectedInvoice.vendor}</div>
                  <div className="text-sm text-gray-600">123 Business Street, Tech City, TC 12345</div>
                  <div className="text-sm text-gray-600">contact@vendor.com • +1 (555) 123-4567</div>
                </div>
                
                <div className="grid grid-cols-2 gap-8 mb-10">
                  <div>
                    <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">Invoice Number</div>
                    <div className="text-gray-900 font-semibold">{selectedInvoice.id.padStart(7, 'INV-000')}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider font-semibold">Date</div>
                    <div className="text-gray-900 font-semibold">{selectedInvoice.date}</div>
                  </div>
                </div>

                <table className="w-full mb-10">
                  <thead>
                    <tr className="border-b-2 border-gray-300">
                      <th className="text-left py-3 text-sm text-gray-700 font-bold">Description</th>
                      <th className="text-right py-3 text-sm text-gray-700 font-bold">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="py-3 text-gray-900">Professional Services</td>
                      <td className="text-right text-gray-900 font-semibold">{selectedInvoice.amount}</td>
                    </tr>
                  </tbody>
                </table>

                <div className="border-t-2 border-gray-300 pt-6 flex justify-between items-center">
                  <span className="text-xl text-gray-900 font-bold">Total Due</span>
                  <span className="text-4xl text-gray-900 font-bold">{selectedInvoice.amount}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Claude Analysis Panel with Cyan Pulse */}
          <div 
            className="w-[420px] p-6 overflow-y-auto border-l backdrop-blur-[20px] relative"
            style={{
              background: 'rgba(6, 7, 9, 0.8)',
              borderColor: 'rgba(255, 255, 255, 0.1)',
            }}
          >
            {/* Cyan Pulse Animation */}
            <div 
              className="absolute inset-0 pointer-events-none"
              style={{
                border: '1px solid rgba(0, 242, 255, 0.3)',
                borderRadius: '0',
                animation: 'cyanPulse 3s ease-in-out infinite',
              }}
            />

            {/* Header */}
            <div className="mb-6 relative z-10">
              <div className="flex items-center gap-2 mb-4">
                <Brain className="w-6 h-6 text-[#00F2FF]" strokeWidth={1.5} />
                <h2 
                  className="text-xl"
                  style={{ 
                    fontFamily: 'Geist Sans, Inter, sans-serif',
                    fontWeight: 700,
                    letterSpacing: '-0.02em',
                  }}
                >
                  AI Analysis
                </h2>
              </div>

              {/* Confidence Gauge */}
              <div 
                className="rounded-lg p-4 mb-4 backdrop-blur-[20px]"
                style={{
                  background: 'rgba(0, 242, 255, 0.05)',
                  border: '1px solid rgba(0, 242, 255, 0.2)',
                }}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-[#71717A] uppercase tracking-wider font-semibold">Confidence Score</span>
                  <span className="text-2xl font-bold display-number text-[#00F2FF]">{selectedInvoice.confidence}%</span>
                </div>
                <div className="h-2 rounded-full bg-[#060709] overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${selectedInvoice.confidence}%`,
                      background: 'linear-gradient(90deg, #00F2FF 0%, #0EA5E9 100%)',
                      filter: 'drop-shadow(0 0 8px rgba(0, 242, 255, 0.5))'
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Analysis Details - Badge style */}
            <div className="space-y-3 mb-6 relative z-10">
              <div 
                className="rounded-lg p-4 backdrop-blur-[20px]"
                style={{
                  background: 'rgba(20, 22, 25, 0.6)',
                  border: '1px solid #FF0055',
                }}
              >
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-[#FF0055] mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-[#FF0055] font-semibold text-sm mb-1">Anomaly Detected</div>
                    <div className="text-[#E5E5E5] text-sm leading-relaxed">{selectedInvoice.reason}</div>
                  </div>
                </div>
              </div>

              <div 
                className="rounded-lg p-4 backdrop-blur-[20px]"
                style={{
                  background: 'rgba(20, 22, 25, 0.6)',
                  border: '1px solid #00FF94',
                }}
              >
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-[#00FF94] mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-[#00FF94] font-semibold text-sm mb-1">Bank Details Verified</div>
                    <div className="text-[#E5E5E5] text-sm leading-relaxed">Account matches vendor records</div>
                  </div>
                </div>
              </div>

              <div 
                className="rounded-lg p-4 backdrop-blur-[20px]"
                style={{
                  background: 'rgba(20, 22, 25, 0.6)',
                  border: '1px solid #00FF94',
                }}
              >
                <div className="flex items-start gap-3">
                  <TrendingUp className="w-5 h-5 text-[#00FF94] mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-[#00FF94] font-semibold text-sm mb-1">Historical Context</div>
                    <div className="text-[#E5E5E5] text-sm leading-relaxed">
                      Average invoice: $10,350. This is 20% higher.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Recommendation */}
            <div 
              className="rounded-lg p-4 mb-6 backdrop-blur-[20px] relative z-10"
              style={{
                background: 'rgba(20, 22, 25, 0.6)',
                border: '1px solid #00F2FF',
              }}
            >
              <div className="text-[#00F2FF] font-semibold text-xs uppercase tracking-wider mb-2">
                AI Recommendation
              </div>
              <div className="text-[#E5E5E5] text-sm leading-relaxed">
                Consider verifying scope of services with vendor before approval.
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2 mb-6 relative z-10">
              <button 
                className="w-full py-3 rounded-lg uppercase tracking-wider text-sm transition-all duration-200 flex items-center justify-center gap-2"
                style={{
                  background: '#00FF94',
                  color: '#060709',
                  fontWeight: 600,
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.2)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'scale(1.02)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                <CheckCircle2 className="w-5 h-5" />
                <span>Approve</span>
              </button>
              
              <button 
                className="w-full py-3 rounded-lg uppercase tracking-wider text-sm transition-all duration-200 flex items-center justify-center gap-2"
                style={{
                  background: 'transparent',
                  color: '#FF0055',
                  border: '1px solid #FF0055',
                  fontWeight: 600,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 0, 85, 0.08)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                <XCircle className="w-5 h-5" />
                <span>Reject</span>
              </button>
            </div>

            {/* Chat with Agent */}
            <div 
              className="rounded-lg p-4 backdrop-blur-[20px] relative z-10"
              style={{
                background: 'rgba(20, 22, 25, 0.6)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
              }}
            >
              <div className="text-[#FAFAFA] font-semibold text-sm mb-3">Chat with AI Agent</div>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Ask a question about this invoice..."
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  className="w-full pl-4 pr-12 py-3 rounded-lg text-sm text-white placeholder-[#52525B] transition-all outline-none"
                  style={{
                    background: 'rgba(6, 7, 9, 0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  onFocus={(e) => {
                    e.target.style.border = '1px solid #00F2FF';
                  }}
                  onBlur={(e) => {
                    e.target.style.border = '1px solid rgba(255, 255, 255, 0.1)';
                  }}
                />
                <button 
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg transition-all"
                  style={{
                    background: chatMessage ? '#00F2FF' : 'rgba(0, 242, 255, 0.2)',
                    color: chatMessage ? '#060709' : '#71717A',
                  }}
                  disabled={!chatMessage}
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* CSS animations */}
      <style>{`
        @keyframes cyanPulse {
          0%, 100% { 
            box-shadow: 0 0 0 0 rgba(0, 242, 255, 0.4);
            border-color: rgba(0, 242, 255, 0.3);
          }
          50% { 
            box-shadow: 0 0 20px 5px rgba(0, 242, 255, 0.2);
            border-color: rgba(0, 242, 255, 0.5);
          }
        }
      `}</style>
    </div>
  );
}
