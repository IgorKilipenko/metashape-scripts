import Metashape
import os
import sys
import time

downscale = 2   # High


def get_doc():
    return Metashape.app.document


def check_project():
    doc = get_doc()
    if not len(doc.chunks) or not len(doc.chunk.cameras):
        raise Exception("Empty project, script aborted")


def execute_align():
    doc = get_doc()
    check_project()

    chunk = doc.chunk

    # Set rolling shutter compensation as full model
    sensor = chunk.cameras[0].sensor
    sensor.rolling_shutter = Metashape.Shutter.Full

    chunk.matchPhotos(downscale=downscale, keypoint_limit=80000, tiepoint_limit=8000,
                      generic_preselection=True, reference_preselection=True,
                      reference_preselection_mode=Metashape.ReferencePreselectionMode.ReferencePreselectionSource,
                      reset_matches=True, filter_stationary_points=True)
    doc.save()

    chunk.alignCameras(min_image=2, adaptive_fitting=False, reset_alignment=True,
                       subdivide_task=True)
    doc.save()

    # Remove bad points
    filter = Metashape.TiePoints.Filter()
    filter.init(chunk, criterion=Metashape.TiePoints.Filter.ImageCount)
    filter.removePoints(threshold=2)
    # filter.selectPoints(threshold=2)
    doc.save()


def execute_dar_workflow():
    doc = get_doc()
    check_project()
    chunk = doc.chunk

    # chunk.buildModel(source_data=Metashape.DepthMapsData)
    # doc.save()

    chunk.optimizeCameras(fit_f=True, fit_cx=True, fit_cy=True, fit_b1=False, fit_b2=False, fit_k1=True,
                          fit_k2=True, fit_k3=True, fit_k4=False, fit_p1=True, fit_p2=True, fit_corrections=True,
                          adaptive_fitting=False, tiepoint_covariance=False)
    doc.save()

    has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

    if has_transform:
        print("Start buildDepthMaps")
        chunk.buildDepthMaps(downscale=downscale,
                             filter_mode=Metashape.MildFiltering)
        print("End buildDepthMaps")
        doc.save()

        print("Start buildPointCloud")
        chunk.buildPointCloud(source_data=Metashape.DepthMapsData, point_colors=True, point_confidence=True,
                              keep_depth=True, max_neighbors=100, uniform_sampling=True, points_spacing=0.1,
                              subdivide_task=True, workitem_size_cameras=20, max_workgroup_size=100)
        print("End buildPointCloud")
        doc.save()

        print("Start buildDem")
        chunk.buildDem(source_data=Metashape.PointCloudData, interpolation=Metashape.EnabledInterpolation, flip_x=False,
                       flip_y=False, flip_z=False, resolution=0, subdivide_task=True, workitem_size_tiles=10, max_workgroup_size=100)
        print("End buildDem")
        doc.save()

        print("Start buildOrthomosaic")
        chunk.buildOrthomosaic(surface_data=Metashape.ElevationData,  blending_mode=Metashape.MosaicBlending, fill_holes=True,
                               ghosting_filter=False, cull_faces=False, refine_seamlines=False, resolution=0, resolution_x=0, resolution_y=0,
                               flip_x=False, flip_y=False, flip_z=False, subdivide_task=True, workitem_size_cameras=20,
                               workitem_size_tiles=10, max_workgroup_size=100)
        print("End buildOrthomosaic")
        doc.save()

    print('Processing finished.')


# Checking compatibility
compatible_major_version = "2.0"
found_major_version = ".".join(Metashape.app.version.split('.')[:2])
if found_major_version != compatible_major_version:
    raise Exception("Incompatible Metashape version: {} != {}".format(
        found_major_version, compatible_major_version))

label = "Scripts/Дар/Выравнивание снимков"
Metashape.app.addMenuItem(label, execute_align)
print("To execute align press {}".format(label))

label_align = "Scripts/Дар/Обработка"
Metashape.app.addMenuItem(label_align, execute_dar_workflow)
print("To execute align press {}".format(label_align))
