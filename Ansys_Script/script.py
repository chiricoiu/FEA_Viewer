import csv

model = db.active_model
db.models['ACP Model'].create_modeling_group( name='ModelingGroup.1' )

with open('surfaces_param.csv') as csv_file:
    csv_reader = csv.reader(csv_file)
    i=1
    for row in csv_reader:
        surface = row[0]
        stackup = row[1]
        rosette = row[2]
        
        name_orientedselectionset = "OrientedSelectionSet." + str(i)
        name_Rosette = "Rosette." + str(rosette)
        name_Stackup = "Stackup." + str(stackup)
        name_ModelingPly = "ModelingPly." + str(i)
        
        db.models['ACP Model'].create_oriented_selection_set(name=name_orientedselectionset)
        
        db.models['ACP Model'].oriented_selection_sets[name_orientedselectionset].element_sets=(db.models['ACP Model'].element_sets[surface])
        db.models['ACP Model'].oriented_selection_sets[name_orientedselectionset].rosettes=(db.models['ACP Model'].rosettes[name_Rosette])
        
        db.models['ACP Model'].modeling_groups['ModelingGroup.1'].create_modeling_ply(name=name_ModelingPly)
        db.models['ACP Model'].modeling_groups['ModelingGroup.1'].plies[name_ModelingPly].oriented_selection_sets = db.models['ACP Model'].oriented_selection_sets[name_orientedselectionset]        
        db.models['ACP Model'].modeling_groups['ModelingGroup.1'].plies[name_ModelingPly].ply_material = db.models['ACP Model'].material_data.stackups[name_Stackup]
        
        i += 1
