import { useState } from "react";

import { askQuestion } from "../services/api";


function ChatBox() {

  const [question, setQuestion] =
    useState("");

  const [answer, setAnswer] =
    useState("");

  const [agent, setAgent] =
    useState("");

  const [sources, setSources] =
    useState([]);

  const [loading, setLoading] =
    useState(false);


  const ask = async () => {

    if (!question.trim()) {
      return;
    }

    try {

      setLoading(true);

      setAnswer("");

      setSources([]);

      const result =
        await askQuestion(question);

      setAnswer(
        result.answer
      );

      setAgent(
        result.agent
      );

      setSources(
        result.sources || []
      );

    } catch (error) {

      console.error(error);

      setAnswer(
        "Unable to process your question."
      );

    } finally {

      setLoading(false);

    }
  };


  return (

    <div className="card">

      <h2>
        Research Assistant
      </h2>


      <textarea

        value={question}

        onChange={(event) =>
          setQuestion(
            event.target.value
          )
        }

        placeholder=
          "Ask something about your research papers..."

      />


      <button
        onClick={ask}
        disabled={loading}
      >

        {loading
          ? "Analyzing..."
          : "Ask Assistant"}

      </button>


      {agent && (

        <div className="agent">

          <strong>
            Agent used:
          </strong>

          {" "}

          {agent}

        </div>

      )}


      {answer && (

        <div className="answer">

          <h3>
            Answer
          </h3>

          <p>
            {answer}
          </p>

        </div>

      )}


      {sources.length > 0 && (

        <div className="sources">

          <h3>
            Sources
          </h3>


          {sources.map(
            (source, index) => (

              <div
                className="source"
                key={index}
              >

                <strong>
                  {source.filename}
                </strong>

                <span>
                  Page {source.page_number}
                </span>

              </div>

            )
          )}

        </div>

      )}

    </div>

  );
}


export default ChatBox;