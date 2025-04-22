import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  useCallback,
} from "react";
import { useNavigate } from "react-router-dom";
import PropTypes from "prop-types";
import { fetchUser } from "../api/auth";

// Create AuthContext
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

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const { data } = await fetchUser(); // Token is included in headers via api/auth.js
      setUser(data);
      setProfileCompleted(data.profile_completed);

    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 403) {
        localStorage.removeItem("token");
        localStorage.removeItem("user_id");
        localStorage.removeItem("username");
        setUser(null);
        setProfileCompleted(false);
        navigate("/login");
      } else {
        console.error("Failed to fetch user:", error.response?.data?.detail || error.message);
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(
    async (token, email = null) => {
      localStorage.setItem("token", token);
      try {
        const { data } = await fetchUser();
        setUser(data);
        setProfileCompleted(data.profile_completed);
        navigate(data.profile_completed ? "/dashboard/posts" : "/complete-profile");
      } catch (error) {
        localStorage.removeItem("token");
        if (error.response?.status === 403) {
          navigate("/verify-email", { state: { email } });
          throw new Error("Please verify your email");
        } else {
          console.error("Failed to fetch user after login:", error.response?.data?.detail || error.message);
          navigate("/login");
          throw new Error("Login failed");
        }
      }
    },
    [navigate]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    setUser(null);
    setProfileCompleted(false);
    navigate("/login");
  }, [navigate]);

  const contextValue = useMemo(
    () => ({ user, profileCompleted, login, logout, loading }),
    [user, profileCompleted, login, logout, loading]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};