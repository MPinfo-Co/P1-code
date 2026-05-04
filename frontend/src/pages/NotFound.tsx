import { Link } from 'react-router-dom'
import './NotFound.css'

export default function NotFound() {
  return (
    <div className="not-found-root">
      <h1 className="not-found-code">404</h1>
      <p className="not-found-text">找不到這個頁面</p>
      <Link to="/" className="not-found-link">
        回首頁
      </Link>
    </div>
  )
}
