import { useAuth } from "../context/AuthContext"; 

const Dashboard = () => {
  const { user, logout } = useAuth(); 

  if (!user) return <p>Loading...</p>; // Show loading until user data is available

  return (
    <div>
      <h2>Welcome, {user.email}</h2>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

export default Dashboard;
