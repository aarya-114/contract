import axios from "axios"
import { useState } from "react"
import PDFViewer from "./components/PDFViewer"

const RISK_COLORS = {
  risky:   { bg: "bg-red-50",    border: "border-red-400",    badge: "bg-red-100 text-red-700",    dot: "🔴" },
  caution: { bg: "bg-yellow-50", border: "border-yellow-400", badge: "bg-yellow-100 text-yellow-700", dot: "🟡" },
  safe:    { bg: "bg-green-50",  border: "border-green-400",  badge: "bg-green-100 text-green-700",  dot: "🟢" },
}

const RISK_LABEL_COLORS = {
  Low:      "text-green-600",
  Medium:   "text-yellow-600",
  High:     "text-orange-600",
  Critical: "text-red-600",
}

function UploadZone({ onUpload, loading }) {
  const [dragging, setDragging] = useState(false)

  const handleFile = (file) => {
    if (file?.type === "application/pdf") onUpload(file)
    else alert("Please upload a PDF file")
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
      className={`border-2 border-dashed rounded-xl p-16 text-center cursor-pointer transition-all
        ${dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"}`}
      onClick={() => document.getElementById("fileInput").click()}
    >
      <input
        id="fileInput"
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />
      {loading ? (
        <div className="space-y-3">
          <div className="text-4xl animate-spin inline-block">⚙️</div>
          <p className="text-gray-600 font-medium">Analyzing contract...</p>
          <p className="text-gray-400 text-sm">This takes 1-2 minutes. Each clause is being analyzed.</p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-5xl">📄</div>
          <p className="text-xl font-semibold text-gray-700">Drop your contract PDF here</p>
          <p className="text-gray-400">or click to browse</p>
          <p className="text-xs text-gray-300 mt-4">Max 10MB • PDF only</p>
        </div>
      )}
    </div>
  )
}

function RiskSummary({ report }) {
  const labelColor = RISK_LABEL_COLORS[report.overall_risk_label] || "text-gray-600"

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-700 mb-4">Contract Risk Summary</h2>
      <div className="flex items-center gap-4 mb-6">
        <div className="text-5xl font-bold text-gray-800">{report.overall_risk_score}</div>
        <div>
          <div className={`text-2xl font-bold ${labelColor}`}>{report.overall_risk_label} Risk</div>
          <div className="text-gray-400 text-sm">out of 100</div>
        </div>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3 mb-6">
        <div
          className={`h-3 rounded-full transition-all ${
            report.overall_risk_score < 20 ? "bg-green-500" :
            report.overall_risk_score < 40 ? "bg-yellow-500" :
            report.overall_risk_score < 65 ? "bg-orange-500" : "bg-red-500"
          }`}
          style={{ width: `${Math.min(report.overall_risk_score, 100)}%` }}
        />
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <div className="text-2xl font-bold text-red-600">{report.risky_count}</div>
          <div className="text-xs text-red-500 mt-1">Risky</div>
        </div>
        <div className="text-center p-3 bg-yellow-50 rounded-lg">
          <div className="text-2xl font-bold text-yellow-600">{report.caution_count}</div>
          <div className="text-xs text-yellow-500 mt-1">Caution</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{report.safe_count}</div>
          <div className="text-xs text-green-500 mt-1">Safe</div>
        </div>
      </div>
      <p className="text-gray-400 text-xs mt-4 text-center">{report.total_clauses} clauses analyzed</p>
    </div>
  )
}

function ClauseCard({ clause, isSelected, onClick }) {
  const [expanded, setExpanded] = useState(isSelected)
  const colors = RISK_COLORS[clause.risk_level] || RISK_COLORS.caution

  return (
    <div
      className={`rounded-xl border-l-4 ${colors.border} ${colors.bg} p-4 transition-all
        ${isSelected ? "ring-2 ring-blue-400 ring-offset-1" : ""}`}
    >
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => { setExpanded(!expanded); onClick?.() }}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">{colors.dot}</span>
          <div>
            <span className="font-semibold text-gray-800">
              {clause.clause_heading || `Clause ${clause.clause_number || clause.clause_index + 1}`}
            </span>
            <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${colors.badge}`}>
              {clause.clause_type}
            </span>
          </div>
        </div>
        <span className="text-gray-400 text-sm">{expanded ? "▲" : "▼"}</span>
      </div>

      <p className="text-gray-600 text-sm mt-2 ml-8">{clause.plain_english}</p>

      {expanded && (
        <div className="mt-3 ml-8 space-y-3">
          <div className="bg-white bg-opacity-60 rounded-lg p-3">
            <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Why this risk level?</p>
            <p className="text-sm text-gray-700">{clause.risk_reasoning}</p>
          </div>
          {clause.negotiation_suggestion && (
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-blue-500 uppercase mb-1">💡 Negotiation Tip</p>
              <p className="text-sm text-blue-700">{clause.negotiation_suggestion}</p>
            </div>
          )}
          {clause.similar_standard_clause && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Compared Against</p>
              <p className="text-sm text-gray-500">{clause.similar_standard_clause}</p>
            </div>
          )}
          <p className="text-xs text-gray-400">{clause.word_count} words</p>
        </div>
      )}
    </div>
  )
}

function ClauseList({ clauses, selectedClause, onClauseSelect }) {
  const [filter, setFilter] = useState("all")
  const filtered = filter === "all" ? clauses : clauses.filter(c => c.risk_level === filter)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-700">Clause Analysis</h2>
        <div className="flex gap-2">
          {["all", "risky", "caution", "safe"].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs px-3 py-1 rounded-full capitalize transition-all ${
                filter === f ? "bg-gray-800 text-white" : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <p className="text-center text-gray-400 py-8">No clauses with this risk level</p>
        ) : (
          filtered.map(clause => (
            <ClauseCard
              key={clause.clause_index}
              clause={clause}
              isSelected={selectedClause === clause.clause_index}
              onClick={() => onClauseSelect?.(clause.clause_index)}
            />
          ))
        )}
      </div>
    </div>
  )
}

// ─── MAIN APP ────────────────────────────────────────────

export default function App() {
  // ✅ ALL state declarations at top
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filename, setFilename] = useState(null)
  const [highlights, setHighlights] = useState([])
  const [pdfUrl, setPdfUrl] = useState(null)
  const [selectedClause, setSelectedClause] = useState(null)

  const handleUpload = async (file) => {
    setLoading(true)
    setError(null)
    setReport(null)
    setFilename(file.name)
    const formData = new FormData()
    formData.append("file", file)
    try {
      const response = await axios.post("/analyze/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 300000
      })
      setReport(response.data)
      setHighlights(response.data.highlights || [])
      setPdfUrl(response.data.pdf_url)
    } catch (err) {
      const msg = err.response?.data?.detail || "Analysis failed. Please try again."
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setReport(null)
    setError(null)
    setFilename(null)
    setHighlights([])
    setPdfUrl(null)
    setSelectedClause(null)
  }

  const loadMockData = () => {
    setFilename("sample-contract.pdf")
    setPdfUrl(null)
    setHighlights([])
    setReport({
      total_clauses: 5,
      risky_count: 2,
      caution_count: 2,
      safe_count: 1,
      overall_risk_score: 45.2,
      overall_risk_label: "Medium",
      clauses: [
        {
          clause_index: 0, clause_number: "1",
          clause_heading: "PAYMENT TERMS", clause_type: "payment",
          risk_level: "risky",
          risk_reasoning: "No penalty cap defined for late payments.",
          plain_english: "You must pay within 30 days or face unlimited 2% monthly interest with no maximum cap.",
          negotiation_suggestion: "Add a maximum penalty cap of 10% of invoice value.",
          similar_standard_clause: "NDA - payment (similarity: 0.89)",
          word_count: 87
        },
        {
          clause_index: 1, clause_number: "2",
          clause_heading: "TERMINATION", clause_type: "termination",
          risk_level: "risky",
          risk_reasoning: "Institute can terminate immediately without compensation.",
          plain_english: "The Institute can end this contract anytime with 30 days notice and owes you nothing extra.",
          negotiation_suggestion: "Request minimum 60 days notice and compensation for work in progress.",
          similar_standard_clause: "Service - termination (similarity: 0.76)",
          word_count: 120
        },
        {
          clause_index: 2, clause_number: "3",
          clause_heading: "CONFIDENTIALITY", clause_type: "confidentiality",
          risk_level: "caution",
          risk_reasoning: "Duration of confidentiality not specified.",
          plain_english: "You must keep all information confidential but the time period is not defined.",
          negotiation_suggestion: "Specify a clear end date, typically 2 years after contract ends.",
          similar_standard_clause: "NDA - confidentiality (similarity: 0.82)",
          word_count: 65
        },
        {
          clause_index: 3, clause_number: "4",
          clause_heading: "DISPUTE RESOLUTION", clause_type: "dispute_resolution",
          risk_level: "caution",
          risk_reasoning: "Arbitration costs borne by both parties equally which may deter claims.",
          plain_english: "Any disputes go to arbitration in Kanpur and both parties pay their own costs.",
          negotiation_suggestion: "Negotiate that losing party pays arbitration costs.",
          similar_standard_clause: "Service - dispute_resolution (similarity: 0.71)",
          word_count: 145
        },
        {
          clause_index: 4, clause_number: "5",
          clause_heading: "FORCE MAJEURE", clause_type: "force_majeure",
          risk_level: "safe",
          risk_reasoning: "Standard force majeure clause covering typical events equally for both parties.",
          plain_english: "If something beyond anyone's control happens like floods or war, obligations are paused fairly for both sides.",
          negotiation_suggestion: null,
          similar_standard_clause: "Service - force_majeure (similarity: 0.91)",
          word_count: 98
        }
      ]
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚖️</span>
            <div>
              <h1 className="text-xl font-bold text-gray-800">ContractSense</h1>
              <p className="text-xs text-gray-400">AI-powered contract risk analysis</p>
            </div>
          </div>
          {report && (
            <button
              onClick={handleReset}
              className="text-sm text-gray-500 hover:text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-100 transition-all"
            >
              ← Analyze another contract
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {!report ? (
          <>
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <p className="text-sm text-blue-700">
                <span className="font-semibold">⚠️ Disclaimer:</span> ContractSense provides
                AI-assisted analysis for informational purposes only. This is not legal advice.
                Always consult a qualified lawyer before signing any contract.
              </p>
            </div>

            <UploadZone onUpload={handleUpload} loading={loading} />

            <button
              onClick={loadMockData}
              className="w-full text-sm text-gray-400 hover:text-gray-600 py-2 border border-dashed border-gray-200 rounded-xl hover:border-gray-300 transition-all"
            >
              Load sample data (for testing)
            </button>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <p className="text-red-700 text-sm">❌ {error}</p>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <span>📄</span>
              <span>{filename}</span>
            </div>

            {/* Two column layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

              {/* Left: PDF Viewer */}
              <div>
                {pdfUrl ? (
                  <PDFViewer
                    pdfUrl={pdfUrl}
                    highlights={highlights}
                    onHighlightClick={(clauseIndex) => setSelectedClause(clauseIndex)}
                  />
                ) : (
                  <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
                    <p className="text-4xl mb-3">📄</p>
                    <p className="text-sm">PDF viewer available after real analysis</p>
                    <p className="text-xs mt-1">Mock data doesn't include a PDF</p>
                  </div>
                )}
              </div>

              {/* Right: Analysis */}
              <div className="space-y-6">
                <RiskSummary report={report} />
                <ClauseList
                  clauses={report.clauses}
                  selectedClause={selectedClause}
                  onClauseSelect={setSelectedClause}
                />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}