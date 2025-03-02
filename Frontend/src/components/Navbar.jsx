import { Link } from "react-router-dom";

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 w-full bg-white shadow-md p-4 flex items-center">
      {/* Clickable Logo */}
      <Link to="/" className="flex items-center">
        <img src="/logo.png" alt="UHub Logo" className="h-10 mr-2 cursor-pointer" />
        <h1 className="text-xl font-bold text-gray-700">UHub</h1>
      </Link>
    </nav>
  );
};

export default Navbar;
