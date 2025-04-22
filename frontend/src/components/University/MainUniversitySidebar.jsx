import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";

export default function UniversitySidebar({ onDeptClick }) {
  const [universities, setUniversities] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/universities")
      .then(res => {
        console.log("Fetched universities:", res.data);
        setUniversities(res.data);
      })
      .catch(err => {
        console.error("Failed to fetch universities:", err);
      });
  }, []);

  return (
    <div className="w-1/4 p-4 border-r overflow-y-auto h-screen">
      {universities.map((uni) => (
        <div key={uni.id} className="mb-4">
          <h2
            className="text-lg font-semibold cursor-pointer text-blue-600 hover:underline"
            onClick={() => {
                console.log("Navigating to:", `/university/${uni.name}`);
                navigate(`/university/${uni.name}`)}}
          >
            {uni.name}
          </h2>
          <ul className="ml-4 text-sm space-y-1">
            {uni.departments.map((dept) => (
              <li
                key={dept}
                className="cursor-pointer text-gray-700 hover:text-blue-500"
                onClick={() => onDeptClick(uni.name, dept)}
              >
                {dept}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
