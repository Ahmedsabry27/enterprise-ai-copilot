import {
  useEffect,
  useRef,
} from "react";


import EmptyState from "./EmptyState";
import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";



export default function ChatWindow({
  messages = [],
  loading = false,
  onPromptClick,
}) {


  const bottomRef = useRef(null);



  // -----------------------------------------
  // Auto Scroll
  // -----------------------------------------

  useEffect(() => {


    bottomRef.current?.scrollIntoView({

      behavior: "smooth",

      block: "end",

    });


  }, [
    messages,
    loading,
  ]);






  return (

    <div
      className="
        flex
        flex-1
        min-h-0
        flex-col
        overflow-hidden
      "
    >




      {/* -------------------------------------
          Conversation Area
      ------------------------------------- */}


      <div
        className="
          flex-1
          overflow-y-auto
          px-8
          pt-8
          pb-48
          scrollbar-thin
          scrollbar-thumb-white/10
          scrollbar-track-transparent
        "
      >





        {
          messages.length === 0 ? (


            <div
              className="
                flex
                min-h-full
                items-center
                justify-center
                animate-in
                fade-in
                duration-500
              "
            >

              <EmptyState
                onPromptClick={onPromptClick}
              />

            </div>


          ) : (



            <div
              className="
                mx-auto
                w-full
                max-w-6xl
                space-y-6
              "
            >


              <MessageList

                messages={
                  messages
                }

              />


            </div>


          )

        }







        {/* -------------------------------------
            Runtime Loading
        ------------------------------------- */}



        {
          loading && (


            <div
              className="
                mx-auto
                mt-6
                w-full
                max-w-6xl
              "
            >

              <TypingIndicator />

            </div>


          )
        }






        {/* Scroll Anchor */}

        <div
          ref={bottomRef}
        />



      </div>


    </div>

  );

}