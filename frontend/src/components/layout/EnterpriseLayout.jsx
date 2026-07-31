import { Outlet } from "react-router-dom";
import {
  Search,
  Bell,
  Settings,
  User,
} from "lucide-react";

import Sidebar from "./Sidebar";


export default function EnterpriseLayout() {


return (

<div
className="
flex
h-screen
overflow-hidden
bg-gradient-to-br
from-[#071426]
via-[#10254d]
to-[#06111f]
text-white
"
>


{/* ======================
    SIDEBAR
====================== */}

<aside
className="
w-72
shrink-0
border-r
border-white/10
bg-black/20
backdrop-blur-2xl
"
>


<Sidebar />


</aside>






{/* ======================
    APPLICATION
====================== */}

<div
className="
flex
flex-1
flex-col
overflow-hidden
"
>





{/* ======================
    TOP BAR
====================== */}


<header
className="
h-20
flex
items-center
justify-between
border-b
border-white/10
bg-white/5
px-8
backdrop-blur-xl
"
>


{/* Search */}


<div
className="
flex
items-center
gap-3
rounded-xl
border
border-white/10
bg-white/5
px-4
py-3
w-[420px]
"
>


<Search
className="
h-5
w-5
text-slate-400
"
/>


<input

placeholder="
Search workflows, agents, actions...
"

className="
bg-transparent
outline-none
text-sm
placeholder:text-slate-500
w-full
"

/>


</div>







{/* Right Side */}

<div
className="
flex
items-center
gap-5
"
>


{/* Runtime */}

<div
className="
flex
items-center
gap-2
rounded-full
border
border-emerald-400/30
bg-emerald-400/10
px-5
py-2
text-sm
text-emerald-300
"
>


<span
className="
h-2
w-2
rounded-full
bg-emerald-400
animate-pulse
"
/>


AI Runtime Online


</div>







<Bell
className="
h-5
w-5
text-slate-300
cursor-pointer
hover:text-white
"
/>



<Settings
className="
h-5
w-5
text-slate-300
cursor-pointer
hover:text-white
"
/>





{/* Profile */}

<div
className="
flex
items-center
gap-3
"
>


<div
className="
h-11
w-11
rounded-full
bg-gradient-to-br
from-blue-500
to-purple-600
flex
items-center
justify-center
font-semibold
shadow-lg
"
>

AS

</div>


</div>



</div>



</header>









{/* ======================
    PAGE CONTENT
====================== */}



<main
className="
flex-1
overflow-y-auto
p-8
"
>


<div
className="
min-h-full
rounded-3xl
border
border-white/10
bg-gradient-to-br
from-white/10
to-white/5
shadow-2xl
backdrop-blur-xl
p-8
"
>


<Outlet />


</div>


</main>




</div>



</div>

);

}