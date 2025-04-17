// src/components/UsernameLink.jsx
import { Link } from 'react-router-dom'

const UsernameLink = ({ username, className = '' }) => {
  if (!username) return null

  return (
    <Link to={`/dashboard/${username}/about`} className={`text-blue-500 hover:underline ${className}`}>
      {username}
    </Link>
  )
}

export default UsernameLink
