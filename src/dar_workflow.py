import Metashape
import os
import sys
import time

def check_project(doc):
    if not len(doc.chunks):
        raise Exception("Empty project, script aborted")

def execute_dar_workflow():
    downscale = 2
    
    doc = Metashape.app.document
    check_project(doc=doc)

    chunk = doc.chunk

    chunk.matchPhotos(downscale=downscale, keypoint_limit=80000, tiepoint_limit=80000,
                    generic_preselection=True, reference_preselection=True,
                    reference_preselection_mode=Metashape.ReferencePreselectionMode.ReferencePreselectionSource,
                    reset_matches=True, filter_stationary_points=True)
    doc.save()

    chunk.alignCameras()
    doc.save()

    chunk.buildDepthMaps(downscale=downscale, filter_mode=Metashape.MildFiltering)
    doc.save()

    chunk.buildModel(source_data=Metashape.DepthMapsData)
    doc.save()

    has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

    if has_transform:
        chunk.buildPointCloud()
        doc.save()

        chunk.buildDem(source_data=Metashape.PointCloudData)
        doc.save()

        chunk.buildOrthomosaic(surface_data=Metashape.ElevationData)
        doc.save()

    print('Processing finished.')

# Checking compatibility
compatible_major_version = "2.0"
found_major_version = ".".join(Metashape.app.version.split('.')[:2])
if found_major_version != compatible_major_version:
    raise Exception("Incompatible Metashape version: {} != {}".format(
        found_major_version, compatible_major_version))

label = "Scripts/dar_workflow"
Metashape.app.addMenuItem(label, execute_dar_workflow)
print("To execute this script press {}".format(label))