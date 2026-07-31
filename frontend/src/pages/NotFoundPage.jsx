export default function NotFoundPage() {

  return (

    <div
      className="
      flex
      min-h-full
      items-center
      justify-center
      "
    >

      <div
        className="
        rounded-3xl
        border
        border-white/10
        bg-white/5
        p-10
        text-center
        backdrop-blur-xl
        "
      >

        <h1
          className="
          text-5xl
          font-bold
          text-white
          "
        >
          404
        </h1>


        <p
          className="
          mt-4
          text-slate-400
          "
        >
          Page not found
        </p>


      </div>

    </div>

  );

}