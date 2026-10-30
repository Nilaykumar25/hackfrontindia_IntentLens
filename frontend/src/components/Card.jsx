import './Card.css'

/**
 * Card container
 * @param {string|React.ElementType} as — default 'div'
 * @param {'flush'} [variant] — flush removes padding
 * @param {boolean} [interactive] — enables hover elevation
 * @param {string} [className]
 */
export default function Card({
  as: Tag = 'div',
  variant,
  interactive = false,
  className = '',
  children,
  ...rest
}) {
  const classes = [
    'card-base',
    variant === 'flush' && 'card-base--flush',
    interactive && 'card-base--interactive',
    className,
  ].filter(Boolean).join(' ')

  return (
    <Tag className={classes} {...rest}>
      {children}
    </Tag>
  )
}
