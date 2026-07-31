import {
  useEffect,
  useState,
  useCallback,
} from "react";


import {
  getConversations,
  getConversationMessages,
  createConversation,
} from "../services/conversationService";





function normalizeConversation(item){

  return {

    ...item,

    id:
      item.id ??
      item.conversation_id,


    title:
      formatTitle(
        item.title
      ),

  };

}





function formatTitle(title){

  if(!title){

    return "New Conversation";

  }


  return title
    .replace(/\s+/g," ")
    .trim()
    .split(" ")
    .map(
      word =>
        word.charAt(0).toUpperCase()
        +
        word.slice(1).toLowerCase()
    )
    .join(" ");

}





function removeDuplicates(items){

  const unique =
    new Map();



  items.forEach(item=>{


    const conversation =
      normalizeConversation(item);



    if(
      conversation.id &&
      !unique.has(conversation.id)
    ){

      unique.set(
        conversation.id,
        conversation
      );

    }


  });



  return Array.from(
    unique.values()
  );

}









export default function useConversation(){



  const [
    conversations,
    setConversations
  ] = useState([]);




  const [
    conversationId,
    setConversationId
  ] = useState(null);




  const [
    selectedConversation,
    setSelectedConversation
  ] = useState(null);




  const [
    loading,
    setLoading
  ] = useState(false);








  // -----------------------------------
  // Load conversations
  // -----------------------------------

  const refreshConversations =
    useCallback(async()=>{


      setLoading(true);



      try{


        const response =
          await getConversations();



        const data =
          Array.isArray(response)
          ?
          response
          :
          response?.data ?? [];



        setConversations(
          removeDuplicates(data)
        );


      }
      catch(error){


        console.error(
          "Failed loading conversations",
          error
        );


        setConversations([]);


      }
      finally{


        setLoading(false);


      }


    },[]);






  // Alias required by useChat
  const loadConversations =
    refreshConversations;







  useEffect(()=>{


    refreshConversations();


  },[
    refreshConversations
  ]);










  // -----------------------------------
  // Create conversation
  // -----------------------------------

  async function ensureConversation(){


    if(conversationId){

      return conversationId;

    }




    try{


      const response =
        await createConversation(
          "New Conversation"
        );



      const id =
        response.id ??
        response.conversation_id;



      setConversationId(id);



      await refreshConversations();



      return id;


    }
    catch(error){


      console.error(
        "Failed creating conversation",
        error
      );


      throw error;


    }


  }









  // -----------------------------------
  // Select conversation
  // -----------------------------------

  function selectConversation(item){



    const conversation =
      typeof item === "object"
      ?
      item
      :
      conversations.find(
        c=>c.id===item
      );




    if(!conversation){

      return;

    }




    setSelectedConversation(
      conversation
    );



    setConversationId(
      conversation.id
    );


  }









  // -----------------------------------
  // Open messages
  // -----------------------------------

  async function openConversation(id){


    try{


      const response =
        await getConversationMessages(id);



      return Array.isArray(response)
      ?
      response
      :
      response?.data ?? [];



    }
    catch(error){


      console.error(
        "Failed loading conversation messages",
        error
      );


      return [];


    }


  }









  // -----------------------------------
  // New chat
  // -----------------------------------

  function newChat(){


    setConversationId(null);


    setSelectedConversation(null);


  }








  // -----------------------------------
  // Reset
  // -----------------------------------

  function resetConversation(){

    setConversationId(null);

    setSelectedConversation(null);

  }








  return {


    conversations,

    loading,


    refreshConversations,

    loadConversations,



    conversationId,

    selectedConversation,



    ensureConversation,


    selectConversation,


    openConversation,


    newChat,

    resetConversation,


  };


}