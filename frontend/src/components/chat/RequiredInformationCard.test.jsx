import {fireEvent,render,screen} from "@testing-library/react";
import {describe,expect,it,vi} from "vitest";
import RequiredInformationCard from "./RequiredInformationCard";

const request={continuation_id:"continuation-1",title:"Additional information required",description:"I need details.",fields:[{name:"project_name",label:"Project",type:"text",required:true},{name:"environment",label:"Environment",type:"select",required:true,options:["staging","production"]}]};

describe("RequiredInformationCard",()=>{
  it("renders schema fields and blocks invalid submission",async()=>{
    const submit=vi.fn();render(<RequiredInformationCard request={request} onSubmit={submit} onCancel={()=>{}}/>);
    expect(screen.getByRole("heading",{name:"Additional information required"})).toHaveFocus();
    fireEvent.click(screen.getByRole("button",{name:/submit details/i}));
    expect(await screen.findByRole("alert")).toHaveTextContent("Complete the marked required fields");
    expect(submit).not.toHaveBeenCalled();
  });

  it("submits values to resume the same continuation",async()=>{
    const submit=vi.fn().mockResolvedValue(undefined);render(<RequiredInformationCard request={request} onSubmit={submit} onCancel={()=>{}}/>);
    fireEvent.change(screen.getByLabelText(/Project/),{target:{value:"Phoenix"}});
    fireEvent.change(screen.getByLabelText(/Environment/),{target:{value:"production"}});
    fireEvent.click(screen.getByRole("button",{name:/submit details/i}));
    expect(submit).toHaveBeenCalledWith({project_name:"Phoenix",environment:"production"});
  });
});
