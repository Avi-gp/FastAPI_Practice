from fastapi import FastAPI , Path , Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel , Field ,computed_field
from typing import Annotated,Literal,Optional
import uvicorn
import json 

app = FastAPI(
    title="FastAPI Server",
    version="1.0",
    description="A simple API server"
)

# Patient Description for Post method
class Patient(BaseModel):
    id: Annotated[str, Field(..., description='ID of the patient', examples=['P001'])]
    name: Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description='Age of the patient')]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender of the patient')]
    height: Annotated[float, Field(..., gt=0, description='Height of the patient in mtrs')]
    weight: Annotated[float, Field(..., gt=0, description='Weight of the patient in kgs')]
    
    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi >= 18.5 and self.bmi < 25:
            return "Normal"
        elif self.bmi >= 25 and self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"
      
      
class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]       
                
#----------------------------------------------------------------------------------------------        

#Json Data Loading Function
def load_data():
    with open("patients.json" , "r") as f:
        data = json.load(f)  
    return data

def save_data(data):
    with open("patients.json" , "w") as f:
        json.dump(data , f , indent=4)

#-------------------------------------------------------------------------------------------
#Get Method
@app.get("/")
async def root():
    return {"message": "Patient Management System API runnig!", "status": "healthy"}

@app.get("/about")
def hello():
    return {"message":"A fully functional patient management system API"}

@app.get("/view")
def view_data():
    data = load_data()
    
    return data

@app.get("/patient/{p_id}")
def view_paitent_data(p_id:str= Path(...,description="Patient ID in the DB", example="P001")):
    data = load_data()
    
    if p_id in data:
        return data[p_id]
    
    raise HTTPException(status_code=404, detail="Patient ID not Found")

@app.get("/sort")
def sort_patient_data(sort_by:str = Query(...,description="Sort data on the basis of age,height or weight"),order:str=Query("asc",description="Sort in asc or desc")):
    valid_fields = ["age", "height","weight"]
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400,detail=f"Invalid field {sort_by}. Please choose from {valid_fields}")
        
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400,detail=f"Invalid order {order}. Please choose between asc and desc")
    
    data = load_data()
    sort_order = True if order=='desc' else False
    sorted_data = sorted(data.values(),key=lambda x:x.get(sort_by,0),reverse = sort_order)
    return sorted_data
    
#--------------------------------------------------------------------------------------------------

#Post method
@app.post("/patient")
def create_patient_data(patient:Patient):
    #load existing data
    data = load_data()
    if patient.id in data:
        raise HTTPException(status_code=400,detail="Patient ID already exists")
    else:
        data[patient.id] = patient.model_dump(exclude=['id'])
        save_data(data)
    return JSONResponse(status_code=200, content={"message": "Patient data created successfully"})
                    
#-----------------------------------------------------------------------------------------------------  
#Put method
@app.put("/patient_edit/{p_id}")
def update_patient_data(patient_update:PatientUpdate , p_id:str=Path(...,description="Patient ID in the DB", example="P001")):
    #load existing data
    data = load_data()
    
    if p_id not in data:
        raise HTTPException(status_code=404,detail="Patient ID not Found")
    
    else:
        existing_patient_info = data[p_id]
        updated_patient_info = patient_update.model_dump(exclude_unset=True)
        #Updating the existing patient info with the new info
        for key , value in updated_patient_info.items():
            existing_patient_info[key] = value
        #Adding the p_id to the new json form after updating     
        existing_patient_info['id'] = p_id
        #Creating Patient pydantic object to update the bmi and verdict if weight or height is changed
        patient_pydantic_obj = Patient(**existing_patient_info)
        #Converting pydantic object into json
        existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')
        #Adding dict to the data
        data[p_id] = existing_patient_info
        #Saving the updated data
        save_data(data)
        
    return JSONResponse(status_code=200, content={"message": "Patient data updated successfully"})
#----------------------------------------------------------------------------------------------------------           
#Delete method
@app.delete("/patient_delete/{p_id}")
def delete_patient_data(p_id:str = Path(...,description="Patient ID in the DB", examples="P001")):
    data = load_data()
    if p_id not in data :
        raise HTTPException(status_code=404 , detail="Patient ID not found")
    else:
        del data[p_id]
        save_data(data)
        return JSONResponse(status_code=200 , content={"message":"Patient data deleted successfully"})

#------------------------------------------------------------------------------------------------------    
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True
    )