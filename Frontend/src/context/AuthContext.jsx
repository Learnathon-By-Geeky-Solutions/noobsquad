import { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { fetchUser } from "../api/auth"; 


const AuthContext = createContext({
  user: null,
  profileCompleted: false,
  login: async () => {},
  logout: () => {},
  loading: true,
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [profileCompleted, setProfileCompleted] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        console.warn("No token found");
        setLoading(false);
        return;
      }

      try {
        console.log("Fetching user with token:", token);
        const userData = await fetchUser(token);
        setUser(userData);
        setProfileCompleted(userData.profile_completed);
      } catch (error) {
        console.error("Failed to fetch user:", error);
        logout();
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (token) => {
    localStorage.setItem("token", token);
    try {
      const response = await fetchUser(token);
      console.log("fetchUser Response:", response); // Debugging API response

      // Check if response contains data
      const userData = response.data || response; 
      console.log("Extracted User Data:", userData);

      setUser(userData);
      setProfileCompleted(userData.profile_completed);
      if (userData.profile_completed){
        navigate("/dashboard")
        console.log("navigating dashboard")
      }
      else{
        navigate("/complete-profile")
        console.log("navigating complete-profile")
      }
      //navigate(userData.profile_completed ? "/dashboard" : "/complete-profile");
    } catch (error) {
      console.error("Failed to fetch user after login:", error);
    }
};


  const logout = () => {
    console.log("Logging out...");
    localStorage.removeItem("token");
    setUser(null);
    setProfileCompleted(false);
    navigate("/login");
  };

  return (
    <AuthContext.Provider value={{ user, profileCompleted, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
