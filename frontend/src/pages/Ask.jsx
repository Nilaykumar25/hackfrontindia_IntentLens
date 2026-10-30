import { useState, useCallback, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ask } from '../api.js'
import AnswerCard from '../components/AnswerCard.jsx'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import Select from '../components/Select.jsx'
import Skeleton from '../components/Skeleton.jsx'
import EvidenceThread from '../components/EvidenceThread.jsx'
import { SUGGESTION_QUESTIONS, THREE_DEMO_QUESTIONS } from '../demoQuestions.js'
import './Ask.css'

/* State variant → CSS modifier and label for demo badges */
const STATE_VARIANT = {
  answered:  { mod: 'answered',   badge: 'Answered'   },
  superseded: { mod: 'superseded', badge: 'Superseded' },
  refused:   { mod: 'refused',    badge: 'Refused'    },
}

/* ── Demo bar (shown only when ?demo=1) ──────────────────── */
function DemoBar({ onSelect, busy }) {
  return (
    <div className="demo-bar" role="region" aria-label="Demo questions">
      <p className="demo-bar__label">
        <span className="demo-bar__badge" aria-hidden="true">Sample</span>
        Click a question to step through the 3-minute demo
      </p>
      <div className="demo-bar__buttons">
        {THREE_DEMO_QUESTIONS.map((dq) => {
          const stateKey = dq.supersededNoticeExpected ? 'superseded' : dq.expectedState
          const variant = STATE_VARIANT[stateKey] || STATE_VARIANT.answered
          return (
            <button
              key={dq.id}
              className={`demo-bar__btn demo-bar__btn--${variant.mod}`}
              onClick={() => onSelect(dq.question)}
              disabled={busy}
              type="button"
              aria-label={`${dq.description} (Sample question)`}
            >
              <span className="demo-bar__btn-label">{dq.question}</span>
              <span className="demo-bar__btn-meta">
                <span className="demo-bar__state-badge" data-state={variant.mod}>
                  {variant.badge}
                </span>
                <span className="demo-bar__sample-tag">Sample</span>
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

const LANG_OPTIONS = [
  { value: 'en',       label: 'English' },
  { value: 'hinglish', label: 'Hinglish' },
  { value: 'hi',       label: 'Hindi' },
]

/* Loading state shows a staged skeleton + stage text */
const STAGES = ['Linking entities', 'Traversing graph', 'Verifying citations']

function LoadingSkeleton({ stage }) {
  return (
    <div className="ask-loading" role="status" aria-live="polite" data-testid="loading-state">
      <p className="ask-loading__stage" aria-atomic="true">
        <span className="ask-loading__dot" aria-hidden="true" />
        {stage}…
      </p>
      {/* Mimics the answer card structure */}
      <div className="ask-loading__skeleton">
        <Skeleton variant="text" width="90%" style={{ marginBottom: 'var(--sp-2)' }} />
        <Skeleton variant="text" width="75%" style={{ marginBottom: 'var(--sp-2)' }} />
        <Skeleton variant="text" width="60%" style={{ marginBottom: 'var(--sp-6)' }} />
        <Skeleton variant="block" height="80px" style={{ marginBottom: 'var(--sp-4)' }} />
        <Skeleton variant="text" width="40%" style={{ marginBottom: 'var(--sp-2)' }} />
        <Skeleton variant="text" width="30%" />
      </div>
    </div>
  )
}

/* Empty state — evidence trail illustration + starter questions */
function EmptyState({ onSelect }) {
  return (
    <div className="ask-empty" data-testid="empty-state">
      <div className="ask-empty__illustration" aria-hidden="true">
        <EvidenceThread size="md" animated={true} decorative={true} />
      </div>
      <p className="ask-empty__label">Every answer traces back through a chain of evidence.</p>
      <div className="ask-empty__starters">
        {SUGGESTION_QUESTIONS.map(q => (
          <button
            key={q}
            className="ask-empty__starter"
            onClick={() => onSelect(q)}
            type="button"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}

/* Error state with retry */
function ErrorState({ message, onRetry }) {
  return (
    <div className="ask-error" role="alert" data-testid="error-state">
      <span className="ask-error__icon" aria-hidden="true">⚠</span>
      <div>
        <p className="ask-error__message">{message}</p>
        <Button variant="ghost" size="sm" onClick={onRetry}>Try again</Button>
      </div>
    </div>
  )
}

/* Question composer — left pane */
function QuestionComposer({ onSubmit, busy, recent }) {
  const [q, setQ] = useState('')
  const [lang, setLang] = useState('en')

  const handleSubmit = useCallback((text) => {
    onSubmit(text || q, lang)
  }, [q, lang, onSubmit])

  return (
    <aside className="ask-composer" aria-label="Question composer">
      <h1 className="ask-composer__title">Ask the codebase</h1>

      <div className="ask-composer__form">
        <Input
          id="question"
          label="Why is the code like this?"
          placeholder="Why is the retry limit three?"
          value={q}
          onChange={e => setQ(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !busy && handleSubmit()}
          disabled={busy}
        />
        <Select
          id="lang"
          label="Language"
          options={LANG_OPTIONS}
          value={lang}
          onChange={e => setLang(e.target.value)}
          disabled={busy}
        />
        <Button
          variant="primary"
          size="md"
          onClick={() => handleSubmit()}
          disabled={busy || !q.trim()}
          loading={busy}
          style={{ width: '100%' }}
        >
          {busy ? 'Searching the graph' : 'Find the decision'}
        </Button>
      </div>

      <section aria-label="Example questions">
        <p className="ask-composer__suggestions-title">Try a question</p>
        <div className="ask-composer__suggestions">
          {SUGGESTION_QUESTIONS.map(ex => (
            <button
              key={ex}
              className="ask-suggestion"
              onClick={() => { setQ(ex); handleSubmit(ex) }}
              disabled={busy}
              type="button"
            >
              {ex}
            </button>
          ))}
        </div>
      </section>

      {recent && recent.length > 0 && (
        <section aria-label="Recent questions">
          <p className="ask-composer__suggestions-title">Recent</p>
          <div className="ask-composer__suggestions">
            {recent.slice(0, 5).map(r => (
              <button
                key={r}
                className="ask-suggestion ask-suggestion--recent"
                onClick={() => { setQ(r); handleSubmit(r) }}
                disabled={busy}
                type="button"
              >
                {r}
              </button>
            ))}
          </div>
        </section>
      )}
    </aside>
  )
}

/* Main export */
export default function Ask() {
  const [searchParams] = useSearchParams()
  const isDemo = searchParams.get('demo') === '1'

  const [state, setState] = useState('empty')
  const [res, setRes]     = useState(null)
  const [errMsg, setErrMsg] = useState('')
  const [stage, setStage] = useState(STAGES[0])
  const [recent, setRecent] = useState([])
  const stageTimer = useRef(null)

  const runStages = useCallback(() => {
    let i = 0
    stageTimer.current = setInterval(() => {
      i = (i + 1) % STAGES.length
      setStage(STAGES[i])
    }, 2200)
    return () => clearInterval(stageTimer.current)
  }, [])

  const submit = useCallback(async (text, lang) => {
    if (!text?.trim()) return
    setState('loading')
    setStage(STAGES[0])
    setRes(null)
    setErrMsg('')

    const stopStages = runStages()
    try {
      const result = await ask(text, lang)
      clearInterval(stageTimer.current)
      setRes(result)
      setState('answered')
      setRecent(prev => [text, ...prev.filter(r => r !== text)].slice(0, 10))
    } catch (e) {
      clearInterval(stageTimer.current)
      setErrMsg(e.message || 'Something went wrong. Is the backend running?')
      setState('error')
    } finally {
      stopStages()
    }
  }, [runStages])

  const retry = useCallback(() => {
    if (res?.question) submit(res.question, 'en')
    else setState('empty')
  }, [res, submit])

  return (
    <div className="ask-shell">
      {isDemo && (
        <DemoBar onSelect={q => submit(q, 'en')} busy={state === 'loading'} />
      )}
      <QuestionComposer onSubmit={submit} busy={state === 'loading'} recent={recent} />

      <main id="main" className="ask-main" aria-label="Answer">
        {state === 'empty'    && <EmptyState onSelect={q => submit(q, 'en')} />}
        {state === 'loading'  && <LoadingSkeleton stage={stage} />}
        {state === 'answered' && res && <AnswerCard res={res} />}
        {state === 'error'    && <ErrorState message={errMsg} onRetry={retry} />}
      </main>
    </div>
  )
}
