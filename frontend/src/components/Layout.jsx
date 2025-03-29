import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";

const Layout = () => {
  return (
    <>
      <Navbar />
      <main className="pt-20"> {/* offset for fixed navbar */}
        <Outlet /> {/* This is where nested pages will render */}
      </main>
    </>
  );
};

export default Layout;
