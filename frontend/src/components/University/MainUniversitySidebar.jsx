import { useEffect, useState } from "react";
import { Building2, GraduationCap } from "lucide-react"; // Optional icons
import { useNavigate } from "react-router-dom";
import api from "../../api";

export default function UniversitySidebar({ onDeptClick }) {
  const [universities, setUniversities] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/universities/")
      .then(res => {
        console.log("Fetched universities:", res.data);
        setUniversities(res.data);
      })
      .catch(err => {
        console.error("Failed to fetch universities:", err);
      });
  }, []);

  return (
    <div className="w-full h-screen overflow-y-auto border-r bg-white p-4 shadow-md">
  <h1 className="text-xl font-bold mb-6 text-gray-800">Explore Universities</h1>
  {universities.map((uni) => (
    <div
      key={uni.id}
      className="mb-6 bg-gray-50 rounded-2xl shadow-sm p-4 hover:shadow-md transition-shadow"
    >
      <h2
        className="flex items-center gap-2 text-blue-700 text-lg font-semibold cursor-pointer hover:underline"
        onClick={() => navigate(`${uni.name}`)}
      >
        <Building2 size={18} /> {uni.name}
      </h2>
      <ul className="ml-1 mt-3 space-y-2">
        {uni.departments.map((dept) => (
          <li
            key={dept}
            className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer hover:text-blue-500"
            onClick={() => onDeptClick(uni.name, dept)}
          >
            <GraduationCap size={16} />
            {dept}
          </li>
        ))}
      </ul>
    </div>
  ))}
</div>
  );
}
