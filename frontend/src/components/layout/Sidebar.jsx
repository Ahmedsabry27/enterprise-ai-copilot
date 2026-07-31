import { NavLink } from "react-router-dom";

import {
  LayoutDashboard,
  MessageSquare,
  Workflow,
  Bot,
  Zap,
  BookOpen,
  ShieldCheck,
  Settings,
  User,
} from "lucide-react";



export default function Sidebar(){


const menu=[

{
name:"Dashboard",
path:"/dashboard",
icon:LayoutDashboard
},

{
name:"Chat",
path:"/chat",
icon:MessageSquare
},

{
name:"Workflows",
path:"/workflows",
icon:Workflow
},

{
name:"Agents",
path:"/agents",
icon:Bot
},

{
name:"Actions",
path:"/actions",
icon:Zap
},
{name:"Knowledge",path:"/knowledge",icon:BookOpen},

{
name:"Audit",
path:"/audit",
icon:ShieldCheck
},

{
name:"Settings",
path:"/settings",
icon:Settings
},


];




return (

<div
className="
flex
h-full
flex-col
p-6
"
>



{/* Brand */}

<div
className="
mb-10
"
>


<h1
className="
text-2xl
font-bold
tracking-tight
text-white
"
>

Enterprise AI

</h1>


<p
className="
text-sm
text-slate-400
"
>

Copilot Platform

</p>


</div>






{/* Navigation */}


<nav
className="
flex-1
space-y-3
"
>


{
menu.map((item)=>{


const Icon=item.icon;


return (

<NavLink

key={item.path}

to={item.path}


className={({isActive})=>`

group
flex
items-center
gap-4
rounded-xl
px-4
py-3
transition-all
duration-300


${
isActive

?

`
bg-gradient-to-r
from-blue-500/30
to-purple-500/20

border
border-blue-400/30

text-white

shadow-lg
shadow-blue-500/10

`

:

`
text-slate-400

hover:text-white

hover:bg-white/10

`
}

`}


>


<Icon

className="
h-5
w-5
transition
group-hover:scale-110
"

/>


<span
className="
text-sm
font-medium
"
>

{item.name}

</span>


</NavLink>


)

})

}



</nav>









{/* User Profile */}


<div

className="
mt-auto
border-t
border-white/10
pt-5
"

>


<div
className="
flex
items-center
gap-3
rounded-xl
bg-white/5
p-3
"
>


<div
className="
flex
h-10
w-10
items-center
justify-center
rounded-full
bg-gradient-to-br
from-blue-500
to-purple-600
font-semibold
"
>

AS

</div>



<div>

<p
className="
text-sm
font-medium
text-white
"
>

Ahmed Sabry

</p>


<p
className="
text-xs
text-slate-400
"
>

Enterprise User

</p>


</div>



</div>


</div>





</div>

)

}
