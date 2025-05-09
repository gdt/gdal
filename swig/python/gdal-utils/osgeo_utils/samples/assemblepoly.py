#!/usr/bin/env python3
###############################################################################
#
# Project:  OGR Python samples
# Purpose:  Assemble polygon geometries from arcs fulled from an arc layer.
#           Script is incomplete but shows use of many OGR features from
#           Python.
# Author:   Frank Warmerdam, warmerdam@pobox.com
#
###############################################################################
# Copyright (c) 2003, Frank Warmerdam <warmerdam@pobox.com>
#
# SPDX-License-Identifier: MIT
###############################################################################

import sys

from osgeo import ogr


def Usage():
    print("Usage: assemblepoly.py [datasource]")
    print("")
    print("  assemblepoly.py  /u/data/ntf/bl2000/HALTON.NTF")
    print("  assemblepoly.py  PG:dbname=test")
    return 2


def doit(name):
    # Open the datasource to operate on.

    # ds = ogr.Open( '/u/data/ntf/bl2000/HALTON.NTF' )
    ds = ogr.Open(name, update=1)

    # layer_count = ds.GetLayerCount()

    # -
    # Establish access to the line and polygon layers.  Eventually we shouldn't
    # hardcode this.

    line_layer = ds.GetLayer(0)
    poly_layer = ds.GetLayer(1)

    #############################################################################
    # Read all features in the line layer, holding just the geometry in a hash
    # for fast lookup by GEOM_ID.

    lines_hash = {}

    feat = line_layer.GetNextFeature()
    geom_id_field = feat.GetFieldIndex("GEOM_ID")
    tile_ref_field = feat.GetFieldIndex("TILE_REF")
    while feat is not None:
        geom_id = feat.GetField(geom_id_field)
        tile_ref = feat.GetField(tile_ref_field)

        if tile_ref not in lines_hash:
            lines_hash[tile_ref] = {}

        sub_hash = lines_hash[tile_ref]
        sub_hash[geom_id] = feat.GetGeometryRef().Clone()

        feat.Destroy()

        feat = line_layer.GetNextFeature()

    print("Got %d lines." % len(lines_hash))

    #############################################################################
    # Read all polygon features.

    feat = poly_layer.GetNextFeature()
    link_field = feat.GetFieldIndex("GEOM_ID_OF_LINK")
    tile_ref_field = feat.GetFieldIndex("TILE_REF")

    while feat is not None:
        tile_ref = feat.GetField(tile_ref_field)
        link_list = feat.GetField(link_field)

        # If the list is in string form we need to convert it.
        if type(link_list).__name__ == "str":
            colon = link_list.find(":")
            items = link_list[colon + 1 : -1].split(",")
            link_list = []
            for item in items:
                try:
                    link_list.append(int(item))
                except Exception:
                    print("item failed to translate: ", item)

        link_coll = ogr.Geometry(type=ogr.wkbGeometryCollection)
        for geom_id in link_list:
            geom = lines_hash[tile_ref][geom_id]
            link_coll.AddGeometry(geom)

        try:
            poly = ogr.BuildPolygonFromEdges(link_coll)
            print(poly.ExportToWkt())
            feat.SetGeometryDirectly(poly)
        except Exception:
            print("BuildPolygonFromEdges failed.")

        # For now we don't actually write back the assembled polygons.
        #    poly_layer.SetFeature( feat )
        feat.Destroy()

        feat = poly_layer.GetNextFeature()


def main(argv=sys.argv, name=None):
    if len(argv) > 1:
        name = argv[1]
    if not name:
        return Usage()
    return doit(name)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
