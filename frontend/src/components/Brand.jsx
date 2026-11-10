function Brand({ title, description }) {
  return (
    <div className="login-brand">
      <div className="brand-icon">
        <i className="bi bi-lightning-charge-fill"></i>
      </div>

      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  )
}

export default Brand