import './Input.css'

/**
 * Controlled text input with label, hint, and error
 * @param {string} label
 * @param {string} id
 * @param {string} [error] — error message shown below
 * @param {string} [hint] — hint text shown below
 */
export default function Input({
  label,
  id,
  error,
  hint,
  className = '',
  ...rest
}) {
  const inputClass = [
    'field__input',
    error && 'field__input--error',
    className,
  ].filter(Boolean).join(' ')

  return (
    <div className="field">
      {label && (
        <label className="field__label" htmlFor={id}>
          {label}
        </label>
      )}
      <input
        id={id}
        className={inputClass}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        aria-invalid={error ? 'true' : undefined}
        {...rest}
      />
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
