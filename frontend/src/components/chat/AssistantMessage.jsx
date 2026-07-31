import Avatar from "./Avatar";
import CopyButton from "./CopyButton";
import MarkdownRenderer from "./MarkdownRenderer";
import RuntimeExecutionCard from "./RuntimeExecutionCard";



export default function AssistantMessage({
  message,
}) {


  const metadata =
    message.metadata || {};



  const content =
    message.content ||
    message.text ||
    "";



  const isWorkflow = Boolean(metadata.execution_id);

  const statusClass =
    metadata.status === "FAILED"
      ? "border-red-400/20 bg-red-400/10 text-red-300"
      : metadata.status === "CANCELLED"
        ? "border-orange-400/20 bg-orange-400/10 text-orange-300"
        : metadata.status === "RUNNING"
          ? "border-blue-400/20 bg-blue-400/10 text-blue-300"
          : "border-emerald-400/20 bg-emerald-400/10 text-emerald-300";





  return (

    <div
      className="
        group
        mb-10
        flex

        animate-in
        fade-in
        slide-in-from-bottom-2

        duration-300
      "
    >




      <div
        className="
          flex
          w-full
          max-w-6xl
          gap-5
        "
      >




        {/* AI Avatar */}

        <div
          className="
            mt-2
          "
        >

          <Avatar />

        </div>








        <div
          className="
            relative
            flex-1
          "
        >







          {/* Copy */}

          {
            content && (


              <div
                className="
                  absolute
                  right-4
                  top-4
                  z-10

                  opacity-0

                  transition

                  group-hover:opacity-100
                "
              >

                <CopyButton
                  text={content}
                />


              </div>


            )
          }










          {/* AI Response */}

          <div
            className="
              rounded-3xl

              border
              border-white/10

              bg-gradient-to-br

              from-white/10

              via-white/5

              to-transparent


              p-6


              shadow-2xl


              backdrop-blur-xl


              text-white


              ring-1

              ring-white/5

            "
          >







            {/* Header */}


            <div
              className="
                mb-5

                flex

                items-center

                justify-between

              "
            >


              <div
                className="
                  flex
                  items-center
                  gap-3
                "
              >



                <div
                  className="
                    flex
                    h-8
                    w-8
                    items-center
                    justify-center

                    rounded-full

                    bg-gradient-to-br

                    from-blue-500

                    to-purple-500
                  "
                >

                  🤖

                </div>




                <div>


                  <p
                    className="
                      font-semibold
                    "
                  >

                    Enterprise AI Copilot

                  </p>


                  <p
                    className="
                      text-xs
                      text-slate-400
                    "
                  >

                    AI Runtime Response

                  </p>


                </div>


              </div>







              {
                metadata.status && (


                  <span
                    className={`
                      rounded-full
                      border
                      px-3
                      py-1
                      text-xs
                      ${statusClass}
                    `}
                  >

                    ● {metadata.status}

                  </span>


                )
              }



            </div>









            {/* Runtime Execution */}

            {
              isWorkflow && (


                <div
                  className="
                    mb-6
                  "
                >

                  <RuntimeExecutionCard

                    metadata={
                      metadata
                    }

                  />

                </div>


              )
            }









            {/* Message Content */}


            {
              content && (


                <div
                  className={

                    isWorkflow

                    ?

                    "border-t border-white/10 pt-6"

                    :

                    ""

                  }
                >


                  <MarkdownRenderer>

                    {content}

                  </MarkdownRenderer>


                </div>


              )
            }









            {/* Execution Summary */}

            {
              isWorkflow && (


                <div
                  className="
                    mt-6

                    grid

                    grid-cols-3

                    gap-4

                    rounded-2xl

                    border

                    border-white/10

                    bg-black/10

                    p-4
                  "
                >



                  <div>

                    <p
                      className="
                        text-xs
                        text-slate-400
                      "
                    >
                      Agent
                    </p>


                    <p>
                      {
                        metadata.agent ||
                        "AI Agent"
                      }
                    </p>

                  </div>





                  <div>

                    <p
                      className="
                        text-xs
                        text-slate-400
                      "
                    >
                      Duration
                    </p>


                    <p>
                      {
                        metadata.duration_ms
                        ||
                        "0"
                      } ms
                    </p>

                  </div>





                  <div>

                    <p
                      className="
                        text-xs
                        text-slate-400
                      "
                    >
                      Workflow
                    </p>


                    <p
                      className="
                        truncate
                      "
                    >
                      {
                        metadata.workflow_id
                      }
                    </p>

                  </div>




                </div>


              )
            }





          </div>




        </div>




      </div>




    </div>


  );

}
