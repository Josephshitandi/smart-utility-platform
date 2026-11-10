function InputField({
  label,
  id,
  name,
  type = 'text',
  placeholder,
  value,
  onChange,
  required = false,
  rightElement,
}) {
  return (
    <div className="mb-3">
      <label htmlFor={id} className="form-label">
        {label}
      </label>

      <div className="position-relative">
        <input
          type={type}
          className="form-control"
          id={id}
          name={name || id}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          required={required}
        />

        {rightElement}
      </div>
    </div>
  )
}

export default InputField