import './Badge.css'

/**
 * Badge / chip for status display
 * @param {'active'|'superseded'|'reversed'|'uncertain'|'refused'|'entity'|'default'} variant
 * @param {'sm'|'md'} size
 */
export default function Badge({
  variant = 'default',
  size = 'sm',
  children,
  className = '',
  ...rest
}) {
  const classes = [
    'badge',
    `badge--${variant}`,
    `badge--${size}`,
    className,
  ].filter(Boolean).join(' ')

  return (
    <span className={classes} {...rest}>
      <span className="badge__dot" aria-hidden="true" />
      {children}
    </span>
  )
}
