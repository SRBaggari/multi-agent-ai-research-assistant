
import PaperUpload from "../components/PaperUpload";

import ChatBox from "../components/ChatBox";


function Dashboard() {

  return (

    <div className="dashboard">

      <header>

        <h1>
          AI Research Assistant
        </h1>

        <p>
          Analyze, compare and explore
          research papers with AI agents.
        </p>

      </header>


      <PaperUpload />

      <ChatBox />

    </div>
  );
}


export default Dashboard;