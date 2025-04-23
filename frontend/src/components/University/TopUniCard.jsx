import { useNavigate } from "react-router-dom";

const TopUniversityCard = ({ topUniversities }) => {
  const navigate = useNavigate();

  return (
    <div className="p-4 shadow-md bg-white rounded-2xl">
      <h3 className="text-lg font-bold mb-4 text-gray-800">Top Universities</h3>
      
      {topUniversities.map((uni, index) => (
        <div
          key={uni.id}
          className="mb-3 cursor-pointer hover:bg-gray-50 p-2 rounded-lg transition"
          onClick={() => navigate(`/university/${uni.name}`)}
        >
          <p className="font-medium text-blue-700 hover:underline">
            {index + 1}. {uni.name}
          </p>
          <p className="text-sm text-gray-500">{uni.total_members} members</p>
        </div>
      ))}

      <div className="mt-4 flex justify-center">
        <button
          variant="outline"
          className="text-sm text-blue-600 border-blue-600 hover:bg-blue-50"
          onClick={() => navigate("/universities")}
        >
          See More
        </button>
      </div>
    </div>
  );
};

export default TopUniversityCard;
