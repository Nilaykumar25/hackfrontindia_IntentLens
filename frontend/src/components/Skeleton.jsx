import './Skeleton.css'

/**
 * Loading skeleton block
 * @param {string} [width] — CSS value, defaults to '100%'
 * @param {string} [height] — CSS value
 * @param {'text'|'block'|'circle'} [variant]
 * @param {string} [className]
 * @param {object} [style] — extra inline styles
 */
export default function Skeleton({
  width,
  height,
  variant = 'block',
  className = '',
  style,
  ...rest
}) {
  const classes = [
    'skeleton',
    `skeleton--${variant}`,
    className,
  ].filter(Boolean).join(' ')

  const inlineStyle = {
    width: width ?? (variant === 'circle' ? height : '100%'),
    height: height ?? (variant === 'text' ? undefined : '20px'),
    ...style,
  }

  return (
    <span
      className={classes}
      style={inlineStyle}
      aria-hidden="true"
      role="presentation"
      {...rest}
    />
  )
}
