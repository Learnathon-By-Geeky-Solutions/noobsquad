import PropTypes from "prop-types";
import { Routes, Route, NavLink } from "react-router-dom";
import { Loader2 } from "lucide-react";

const ResearchTabView = ({ title, basePath, tabs }) => {
  return (
    <div className="bg-gray-50 min-h-screen mt-20 md:mt-24">
      <div className="pt-6 pb-2 text-center">
        <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
      </div>

      <div className=" rounded-xl mx-auto max-w-6xl px-4 py-4 mb-6">
        <ul className="flex flex-wrap justify-center gap-4">
          {tabs.map(({ path, label, icon, loading, badge }) => (
            <NavTab
              key={path}
              to={`${basePath}/${path}`}
              label={label}
              icon={icon}
              loading={loading}
              badge={badge}
            />
          ))}
        </ul>
      </div>

      <div className="max-w-6xl mx-auto p-6 ">
        <Routes>
          {tabs.map(({ path, element }) => (
            <Route key={path} path={path} element={element} />
          ))}
        </Routes>
      </div>
    </div>
  );
};

const NavTab = ({ to, label, icon: Icon, loading = false, badge = null }) => (
  <li>
    <NavLink
      to={to}
      className={({ isActive }) =>
        `relative inline-flex items-center gap-2 px-4 py-2 rounded-full font-medium text-sm transition ${
          isActive
            ? "bg-blue-600 text-white shadow"
            : "bg-gray-100 text-gray-700 hover:bg-blue-100 hover:text-blue-600"
        }`
      }
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Icon className="w-4 h-4" />
      )}
      {label}
      {badge !== null && (
        <span className="absolute -top-1 -right-2 bg-red-500 text-white text-[10px] px-1.5 py-0.5 rounded-full font-semibold">
          {badge}
        </span>
      )}
    </NavLink>
  </li>
);

NavTab.propTypes = {
  to: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  icon: PropTypes.elementType.isRequired,
  loading: PropTypes.bool,
  badge: PropTypes.number,
};

ResearchTabView.propTypes = {
  title: PropTypes.string.isRequired,
  basePath: PropTypes.string.isRequired,
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      path: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      icon: PropTypes.elementType.isRequired,
      element: PropTypes.element.isRequired,
      loading: PropTypes.bool,
      badge: PropTypes.number,
    })
  ).isRequired,
};

export default ResearchTabView;
