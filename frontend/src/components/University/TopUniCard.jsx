import { useNavigate } from "react-router-dom";
import React, { useEffect, useState } from "react";
import api from "../../api";

const TopUniversityCard = () => {
  const [topUniversities, setTopUniversities] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTopUniversities = async () => {
      try {
        const response = await api.get("/top/top-universities");
        setTopUniversities(response.data);
      } catch (error) {
        console.error("Failed to fetch top universities:", error);
      }
    };

    fetchTopUniversities();
  }, []);

  return (
    <div className="p-4 shadow-md bg-white rounded-2xl">
      <h3 className="text-lg font-bold mb-4 text-gray-800">Connected Universities</h3>
      
      {topUniversities.map((uni) => (
        <div
          key={uni.id}
          className="mb-3 cursor-pointer hover:bg-gray-50 p-2 rounded-lg transition"
          onClick={() => navigate(`/dashboard/university/${uni.name}`)}
        >
          <p className="font-medium text-blue-700 hover:underline">
             {uni.name}
          </p>
          <p className="text-sm text-gray-500">{uni.total_members} members</p>
        </div>
      ))}

      <div className="mt-4 flex justify-center">
        <button
          variant="outline"
          className="text-sm text-blue-600 border-blue-600 hover:bg-blue-50"
          onClick={() => navigate("/dashboard/university")}
        >
          See More
        </button>
      </div>
    </div>
  );
};

export default TopUniversityCard;
