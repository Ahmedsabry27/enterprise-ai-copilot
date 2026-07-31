export default function EmptyState({
  onPromptClick,
}) {


  const suggestions = [

    "Generate Deployment Report",

    "Analyze Release Risk",

    "Run Compliance Check",

    "Analyze Metrics",

  ];



  return (

    <div
      className="
        flex
        h-full
        items-center
        justify-center
      "
    >


      <div
        className="
          max-w-xl
          text-center
        "
      >


        <div
          className="
            mx-auto
            mb-6
            flex
            h-20
            w-20
            items-center
            justify-center
            rounded-full
            bg-emerald-400/20
            text-3xl
          "
        >

          🤖

        </div>





        <h1
          className="
            text-4xl
            font-bold
            text-white
          "
        >

          Enterprise AI Copilot

        </h1>





        <p
          className="
            mt-3
            text-slate-400
          "
        >

          Your AI workforce is ready to help you execute enterprise workflows.

        </p>







        <div
          className="
            mt-8
            grid
            grid-cols-2
            gap-4
          "
        >



          {
            suggestions.map(
              (item)=>(
                

                <button

                  key={item}

                  onClick={() =>
                    onPromptClick?.(item)
                  }

                  className="
                    rounded-xl
                    border
                    border-white/10
                    bg-white/5
                    p-5
                    text-left
                    text-white
                    transition
                    hover:bg-white/10
                    hover:border-blue-400/40
                    cursor-pointer
                  "

                >

                  <span
                    className="
                      mr-2
                    "
                  >
                    ✨
                  </span>


                  {item}


                </button>


              )
            )
          }



        </div>



      </div>


    </div>

  );

}