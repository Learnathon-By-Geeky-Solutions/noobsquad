const MemberCard = ({ username, email }) => {
    return (
      <div className="text-sm text-gray-700 border-b py-1 flex justify-between items-center">
        <span>@{username}</span>
        <span className="text-xs text-gray-500">{email}</span>
      </div>
    );
  };
  
  export default MemberCard;