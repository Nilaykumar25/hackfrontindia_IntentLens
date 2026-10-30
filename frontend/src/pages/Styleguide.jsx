import Badge from '../components/Badge.jsx'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import EvidenceThread from '../components/EvidenceThread.jsx'
import Input from '../components/Input.jsx'
import Select from '../components/Select.jsx'
import Skeleton from '../components/Skeleton.jsx'

/* ── Contrast data (all pre-calculated) ──────────────────── */
const CONTRASTS = [
  { label: 'Dark: --ink (#e6edf3) on --bg (#0d1117)',        ratio: 15.9, fg: '#e6edf3', bg: '#0d1117', req: 4.5 },
  { label: 'Dark: --ink (#e6edf3) on --surface (#161b22)',   ratio: 14.4, fg: '#e6edf3', bg: '#161b22', req: 4.5 },
  { label: 'Dark: --muted (#8b949e) on --bg (#0d1117)',      ratio: 6.4,  fg: '#8b949e', bg: '#0d1117', req: 4.5 },
  { label: 'Dark: --accent-fg (#0d1117) on --accent (#e8a838) [button]', ratio: 8.1, fg: '#0d1117', bg: '#e8a838', req: 4.5 },
  { label: 'Dark: --accent (#e8a838) on --surface (#161b22) [text]',     ratio: 7.4, fg: '#e8a838', bg: '#161b22', req: 4.5 },
  { label: 'Light: --ink (#1f2328) on --bg (#f6f8fa)',       ratio: 13.5, fg: '#1f2328', bg: '#f6f8fa', req: 4.5 },
  { label: 'Light: --ink (#1f2328) on --surface (#ffffff)',  ratio: 14.4, fg: '#1f2328', bg: '#ffffff', req: 4.5 },
  { label: 'Light: --muted (#59636e) on --bg (#f6f8fa)',     ratio: 6.0,  fg: '#59636e', bg: '#f6f8fa', req: 4.5 },
  { label: 'Light: --accent-fg (#ffffff) on --accent (#b8821f) [button]', ratio: 4.78, fg: '#ffffff', bg: '#b8821f', req: 4.5 },
  { label: 'Light: --accent (#b8821f) on --surface (#ffffff) [text]',     ratio: 4.78, fg: '#b8821f', bg: '#ffffff', req: 4.5 },
  { label: 'Dark badge: #3fb950 on --surface-2 (#1c232c)',   ratio: 3.66, fg: '#3fb950', bg: '#1c232c', req: 3.0 },
  { label: 'Light badge: #1a7f37 on #eef1f4',                ratio: 7.34, fg: '#1a7f37', bg: '#eef1f4', req: 3.0 },
]

/* ── Section wrapper ─────────────────────────────────────── */
function Section({ title, children }) {
  return (
    <section style={{ marginBottom: 'var(--sp-16)' }}>
      <h2 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-h2)',
        marginBottom: 'var(--sp-6)',
        paddingBottom: 'var(--sp-3)',
        borderBottom: '1px solid var(--line)',
        color: 'var(--ink)',
      }}>
        {title}
      </h2>
      {children}
    </section>
  )
}

/* ── Row layout helper ───────────────────────────────────── */
function Row({ children, wrap = true }) {
  return (
    <div style={{
      display: 'flex',
      gap: 'var(--sp-4)',
      flexWrap: wrap ? 'wrap' : 'nowrap',
      alignItems: 'center',
    }}>
      {children}
    </div>
  )
}

/* ── Swatch ──────────────────────────────────────────────── */
function Swatch({ name, value, dark = false }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{
        width: 80,
        height: 48,
        background: value,
        borderRadius: 'var(--r-sm)',
        border: '1px solid var(--line)',
      }} />
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink)', fontFamily: 'var(--font-mono)' }}>{name}</span>
      <span style={{ fontSize: 9, color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>{value}</span>
    </div>
  )
}

/* ── Type specimen ───────────────────────────────────────── */
function TypeSpec({ name, sample, style: s }) {
  return (
    <div style={{ marginBottom: 'var(--sp-4)', display: 'flex', alignItems: 'baseline', gap: 'var(--sp-6)' }}>
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted)', fontFamily: 'var(--font-mono)', minWidth: 120 }}>
        {name}
      </span>
      <span style={s}>{sample || 'The evidence trail'}</span>
    </div>
  )
}

export default function Styleguide() {
  return (
    <main id="main" style={{ padding: 'var(--sp-10) var(--sp-6)', maxWidth: 'var(--max-layout)', margin: '0 auto' }}>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-h1)', marginBottom: 'var(--sp-2)' }}>
        Styleguide
      </h1>
      <p style={{ color: 'var(--muted)', marginBottom: 'var(--sp-12)', fontSize: 'var(--text-sm)' }}>
        Component reference — visible in development only.
      </p>

      {/* ── Typography ─────────────────────────────────────── */}
      <Section title="Typography">
        <TypeSpec name="--text-hero" style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-hero)', lineHeight: 1.05, fontWeight: 500 }} />
        <TypeSpec name="h1 --text-h1" style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-h1)', lineHeight: 1.25, fontWeight: 500 }} />
        <TypeSpec name="h2 --text-h2" style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-h2)', lineHeight: 1.25, fontWeight: 500 }} />
        <TypeSpec name="h3 --text-h3" style={{ fontFamily: 'var(--font-ui)', fontSize: 'var(--text-h3)', lineHeight: 1.35, fontWeight: 500 }} />
        <TypeSpec name="body --text-body" style={{ fontFamily: 'var(--font-ui)', fontSize: 'var(--text-body)', lineHeight: 1.6 }} />
        <TypeSpec name="read --text-read" sample="Fraunces at reading size — the evidence trail." style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-read)', lineHeight: 1.75 }} />
        <TypeSpec name="sm --text-sm" style={{ fontFamily: 'var(--font-ui)', fontSize: 'var(--text-sm)' }} />
        <TypeSpec name="xs --text-xs" style={{ fontFamily: 'var(--font-ui)', fontSize: 'var(--text-xs)', fontWeight: 500 }} />
        <TypeSpec name="mono --text-mono" sample="replication.c:482 — sds_create()" style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-mono)' }} />
      </Section>

      {/* ── Colour palette ─────────────────────────────────── */}
      <Section title="Colour palette">
        <h3 style={{ fontSize: 'var(--text-h3)', marginBottom: 'var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Backgrounds</h3>
        <Row>
          <Swatch name="--bg" value="var(--bg)" />
          <Swatch name="--surface" value="var(--surface)" />
          <Swatch name="--surface-2" value="var(--surface-2)" />
          <Swatch name="--surface-3" value="var(--surface-3)" />
        </Row>
        <h3 style={{ fontSize: 'var(--text-h3)', margin: 'var(--sp-6) 0 var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Text</h3>
        <Row>
          <Swatch name="--ink" value="var(--ink)" />
          <Swatch name="--ink-2" value="var(--ink-2)" />
          <Swatch name="--muted" value="var(--muted)" />
          <Swatch name="--line" value="var(--line)" />
        </Row>
        <h3 style={{ fontSize: 'var(--text-h3)', margin: 'var(--sp-6) 0 var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Accent</h3>
        <Row>
          <Swatch name="--accent" value="var(--accent)" />
          <Swatch name="--accent-hover" value="var(--accent-hover)" />
          <Swatch name="--accent-soft" value="var(--accent-soft)" />
          <Swatch name="--accent-fg" value="var(--accent-fg)" />
        </Row>
        <h3 style={{ fontSize: 'var(--text-h3)', margin: 'var(--sp-6) 0 var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Status</h3>
        <Row>
          <Swatch name="--active" value="var(--active)" />
          <Swatch name="--superseded" value="var(--superseded)" />
          <Swatch name="--reversed" value="var(--reversed)" />
          <Swatch name="--uncertain" value="var(--uncertain)" />
          <Swatch name="--refused" value="var(--refused)" />
          <Swatch name="--entity" value="var(--entity)" />
        </Row>
      </Section>

      {/* ── Buttons ────────────────────────────────────────── */}
      <Section title="Buttons">
        <h3 style={{ fontSize: 'var(--text-h3)', marginBottom: 'var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Primary</h3>
        <Row>
          <Button variant="primary" size="sm">Small</Button>
          <Button variant="primary" size="md">Medium</Button>
          <Button variant="primary" size="lg">Large</Button>
          <Button variant="primary" disabled>Disabled</Button>
          <Button variant="primary" loading>Loading</Button>
        </Row>
        <h3 style={{ fontSize: 'var(--text-h3)', margin: 'var(--sp-6) 0 var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Secondary</h3>
        <Row>
          <Button variant="secondary" size="sm">Small</Button>
          <Button variant="secondary" size="md">Medium</Button>
          <Button variant="secondary" size="lg">Large</Button>
          <Button variant="secondary" disabled>Disabled</Button>
        </Row>
        <h3 style={{ fontSize: 'var(--text-h3)', margin: 'var(--sp-6) 0 var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Ghost</h3>
        <Row>
          <Button variant="ghost" size="sm">Small</Button>
          <Button variant="ghost" size="md">Medium</Button>
          <Button variant="ghost" size="lg">Large</Button>
          <Button variant="ghost" disabled>Disabled</Button>
        </Row>
      </Section>

      {/* ── Badges ─────────────────────────────────────────── */}
      <Section title="Badges">
        <Row>
          <Badge variant="active">Active</Badge>
          <Badge variant="superseded">Superseded</Badge>
          <Badge variant="reversed">Reversed</Badge>
          <Badge variant="uncertain">Uncertain</Badge>
          <Badge variant="refused">Refused</Badge>
          <Badge variant="entity">Entity</Badge>
          <Badge variant="default">Default</Badge>
        </Row>
        <div style={{ marginTop: 'var(--sp-4)' }}>
          <Row>
            <Badge variant="active" size="md">Active md</Badge>
            <Badge variant="entity" size="md">Entity md</Badge>
            <Badge variant="reversed" size="md">Reversed md</Badge>
          </Row>
        </div>
      </Section>

      {/* ── Card ───────────────────────────────────────────── */}
      <Section title="Card">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--sp-4)' }}>
          <Card>
            <h3 style={{ fontFamily: 'var(--font-ui)', fontSize: 'var(--text-h3)', marginBottom: 'var(--sp-2)' }}>Default card</h3>
            <p style={{ color: 'var(--muted)', fontSize: 'var(--text-sm)' }}>Surface background, border, standard padding.</p>
          </Card>
          <Card interactive>
            <h3 style={{ fontFamily: 'var(--font-ui)', fontSize: 'var(--text-h3)', marginBottom: 'var(--sp-2)' }}>Interactive card</h3>
            <p style={{ color: 'var(--muted)', fontSize: 'var(--text-sm)' }}>Hover shows elevation. No transition on every card.</p>
          </Card>
          <Card variant="flush">
            <div style={{ padding: 'var(--sp-4)', background: 'var(--accent-soft)', borderRadius: 'var(--r-md)' }}>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--accent)' }}>Flush variant — custom content fills edge to edge.</p>
            </div>
          </Card>
        </div>
      </Section>

      {/* ── Input ──────────────────────────────────────────── */}
      <Section title="Input">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--sp-6)' }}>
          <Input id="sg-input-1" label="Label" placeholder="Placeholder text" hint="This is a hint" />
          <Input id="sg-input-2" label="With error" placeholder="Something went wrong" error="This field is required" />
          <Input id="sg-input-3" label="Disabled" placeholder="Not editable" disabled />
        </div>
      </Section>

      {/* ── Select ─────────────────────────────────────────── */}
      <Section title="Select">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 'var(--sp-6)' }}>
          <Select
            id="sg-select-1"
            label="Language"
            hint="Choose the response language"
            options={[
              { value: 'en', label: 'English' },
              { value: 'hinglish', label: 'Hinglish' },
              { value: 'hi', label: 'Hindi' },
            ]}
          />
          <Select
            id="sg-select-2"
            label="With error"
            error="Please select an option"
            options={[
              { value: '', label: '— select —' },
              { value: 'a', label: 'Option A' },
            ]}
          />
        </div>
      </Section>

      {/* ── Skeleton ───────────────────────────────────────── */}
      <Section title="Skeleton">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)', maxWidth: 480 }}>
          <div>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--muted)', marginBottom: 'var(--sp-2)' }}>Text variant</p>
            <Skeleton variant="text" />
            <Skeleton variant="text" width="75%" />
            <Skeleton variant="text" width="50%" />
          </div>
          <div>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--muted)', marginBottom: 'var(--sp-2)' }}>Block variant</p>
            <Skeleton variant="block" height="80px" />
          </div>
          <div>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--muted)', marginBottom: 'var(--sp-2)' }}>Circle variant</p>
            <Skeleton variant="circle" height="48px" />
          </div>
        </div>
      </Section>

      {/* ── EvidenceThread ─────────────────────────────────── */}
      <Section title="EvidenceThread">
        <h3 style={{ fontSize: 'var(--text-h3)', marginBottom: 'var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Animated (lg)</h3>
        <EvidenceThread size="lg" animated={true} />

        <h3 style={{ fontSize: 'var(--text-h3)', margin: 'var(--sp-8) 0 var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Static (md)</h3>
        <EvidenceThread size="md" animated={false} />

        <h3 style={{ fontSize: 'var(--text-h3)', margin: 'var(--sp-8) 0 var(--sp-4)', fontFamily: 'var(--font-ui)' }}>Small</h3>
        <EvidenceThread size="sm" animated={false} />
      </Section>

      {/* ── Contrast report ────────────────────────────────── */}
      <Section title="Contrast report (WCAG AA)">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {CONTRASTS.map(({ label, ratio, fg, bg, req }) => {
            const pass = ratio >= req
            return (
              <div
                key={label}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--sp-4)',
                  padding: 'var(--sp-3) var(--sp-4)',
                  background: 'var(--surface)',
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--r-sm)',
                  borderLeft: `4px solid ${pass ? 'var(--active)' : 'var(--reversed)'}`,
                }}
              >
                <div style={{
                  width: 40,
                  height: 24,
                  background: bg,
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--r-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <span style={{ color: fg, fontSize: 10, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>Aa</span>
                </div>
                <span style={{ flex: 1, fontSize: 'var(--text-xs)', color: 'var(--ink)', fontFamily: 'var(--font-ui)' }}>
                  {label}
                </span>
                <span style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--muted)',
                  flexShrink: 0,
                }}>
                  {ratio.toFixed(1)}:1
                </span>
                <Badge variant={pass ? 'active' : 'reversed'} size="sm">
                  {pass ? 'PASS' : 'FAIL'}
                </Badge>
                <span style={{ fontSize: 9, color: 'var(--muted)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                  req {req}:1
                </span>
              </div>
            )
          })}
        </div>
      </Section>
    </main>
  )
}
