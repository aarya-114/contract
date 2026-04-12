import { useRef, useState } from "react"
import { Document, Page, pdfjs } from "react-pdf"
import "react-pdf/dist/Page/AnnotationLayer.css"
import "react-pdf/dist/Page/TextLayer.css"

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString()

const RISK_HIGHLIGHT_COLORS = {
  risky:   "rgba(239, 68, 68, 0.35)",
  caution: "rgba(234, 179, 8, 0.35)",
  safe:    "rgba(34, 197, 94, 0.35)",
}

const PDF_SCALE = 1.2

export default function PDFViewer({ pdfUrl, highlights, onHighlightClick }) {
  const [numPages, setNumPages] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const containerRef = useRef(null)

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages)
  }

  const getPageHighlights = (pageNum) => {
    return highlights.filter(h => h.page === pageNum - 1)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">

      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-700">PDF Viewer</span>
          <div className="flex gap-2 text-xs">
            <span className="px-2 py-0.5 bg-red-100 text-red-600 rounded-full">🔴 Risky</span>
            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-600 rounded-full">🟡 Caution</span>
            <span className="px-2 py-0.5 bg-green-100 text-green-600 rounded-full">🟢 Safe</span>
          </div>
        </div>

        {numPages && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-2 py-1 rounded hover:bg-gray-200 disabled:opacity-30"
            >
              ←
            </button>
            <span>Page {currentPage} of {numPages}</span>
            <button
              onClick={() => setCurrentPage(p => Math.min(numPages, p + 1))}
              disabled={currentPage === numPages}
              className="px-2 py-1 rounded hover:bg-gray-200 disabled:opacity-30"
            >
              →
            </button>
          </div>
        )}
      </div>

      {/* PDF + Highlights */}
      <div
        ref={containerRef}
        className="overflow-auto bg-gray-100 flex justify-center p-4"
        style={{ maxHeight: "85vh" }}
      >
        <div style={{ position: "relative", display: "inline-block" }}>
          <Document
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="flex items-center justify-center p-16">
                <p className="text-gray-400">Loading PDF...</p>
              </div>
            }
            error={
              <div className="flex items-center justify-center p-16">
                <p className="text-red-400">Failed to load PDF</p>
              </div>
            }
          >
            <Page
              pageNumber={currentPage}
              scale={PDF_SCALE}
              renderTextLayer={true}
              renderAnnotationLayer={false}
            />
          </Document>

          {/* Highlight Overlays */}
          {getPageHighlights(currentPage).map((highlight, i) => {
            const color = RISK_HIGHLIGHT_COLORS[highlight.risk_level] || RISK_HIGHLIGHT_COLORS.caution

            // scaleFactor = PDF_SCALE only
            // react-pdf handles DPI internally
            // Previous 96/72 multiplier was causing misalignment
            const scaleFactor = PDF_SCALE

            const style = {
              position: "absolute",
              left:   highlight.rect[0] * scaleFactor,
              top:    highlight.rect[1] * scaleFactor,
              width:  (highlight.rect[2] - highlight.rect[0]) * scaleFactor,
              height: (highlight.rect[3] - highlight.rect[1]) * scaleFactor,
              backgroundColor: color,
              borderRadius: "2px",
              cursor: "pointer",
              pointerEvents: "auto",
              transition: "opacity 0.2s",
              zIndex: 10,
            }

            return (
              <div
                key={i}
                style={style}
                onClick={() => onHighlightClick(highlight.clause_index)}
                title={`${highlight.clause_heading || highlight.clause_number} — Click to see analysis`}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}