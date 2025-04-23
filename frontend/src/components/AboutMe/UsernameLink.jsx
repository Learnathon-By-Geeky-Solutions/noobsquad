// src/components/UsernameLink.jsx
import { Link } from 'react-router-dom'

const UsernameLink = ({ username, className = '' }) => {
  if (!username) return null

  return (
    <Link to={`/dashboard/${username}/about`} className={`text-black-500 ${className}`}>
      {username}
    </Link>
  )
}

export default UsernameLink
