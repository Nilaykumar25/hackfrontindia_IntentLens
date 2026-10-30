import './Select.css'

/**
 * Styled select wrapper
 * @param {string} label
 * @param {string} id
 * @param {{value: string, label: string}[]} options
 * @param {string} [error]
 */
export default function Select({
  label,
  id,
  options = [],
  error,
  hint,
  className = '',
  ...rest
}) {
  const selectClass = [
    'field__select',
    error && 'field__select--error',
    className,
  ].filter(Boolean).join(' ')

  return (
    <div className="field">
      {label && (
        <label className="field__label" htmlFor={id}>
          {label}
        </label>
      )}
      <div className="select-wrapper">
        <select
          id={id}
          className={selectClass}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          aria-invalid={error ? 'true' : undefined}
          {...rest}
        >
          {options.map(({ value, label: optLabel }) => (
            <option key={value} value={value}>
              {optLabel}
            </option>
          ))}
        </select>
        <span className="select-wrapper__icon" aria-hidden="true">
          <ChevronIcon />
        </span>
      </div>
      {error && (
        <span id={`${id}-error`} className="field__error" role="alert">
          {error}
        </span>
      )}
      {hint && !error && (
        <span id={`${id}-hint`} className="field__hint">
          {hint}
        </span>
      )}
    </div>
  )
}

function ChevronIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
