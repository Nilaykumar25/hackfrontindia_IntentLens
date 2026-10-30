import './Button.css'

/**
 * Button component
 * @param {object} props
 * @param {'primary'|'secondary'|'ghost'} props.variant
 * @param {'sm'|'md'|'lg'} props.size
 * @param {string|React.ElementType} props.as — render as anchor or other element
 * @param {boolean} props.disabled
 * @param {boolean} props.loading — shows spinner, disables interaction
 * @param {string} [props.className]
 * @param {React.ReactNode} props.children
 */
export default function Button({
  variant = 'primary',
  size = 'md',
  as: Tag = 'button',
  disabled = false,
  loading = false,
  className = '',
  children,
  ...rest
}) {
  const classes = [
    'btn',
    `btn--${variant}`,
    `btn--${size}`,
    className,
  ].filter(Boolean).join(' ')

  const isDisabled = disabled || loading

  return (
    <Tag
      className={classes}
      disabled={Tag === 'button' ? isDisabled : undefined}
      aria-disabled={Tag !== 'button' ? isDisabled : undefined}
      {...rest}
    >
      {loading && (
        <span className="btn__spinner" aria-hidden="true" />
      )}
      {children}
    </Tag>
  )
}
