#!/usr/bin/env python


"""Take images, crop the same bit from each, put side-by-side.


Useful for comparing e.g. lenses, f-stops
"""



from __future__ import print_function, division

import os
import sys
import argparse
import subprocess


import PIL.ExifTags
import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw

from wand.image import Image


def exif_tuple_to_float(x):
    return float(x[0]) / float(x[1])


def determine_arrangement(n_inputs):
    """Determine (n_row, n_col) for n_inputs"""
    arrangement_dict = {
        1 : (1, 1),
        2 : (1, 2),
        3 : (1, 3),
        4 : (2, 2),
        5 : (2, 3),
        6 : (2, 3),
        7 : (2, 4),
        8 : (2, 8),
        9 : (3, 3),
        10 : (2, 5),
        11 : (3, 4),
        12 : (3, 4),
        13 : (2, 7),
        14 : (2, 7),
        15 : (3, 5),
        16 : (4, 4),
    }
    if n_inputs not in arrangement_dict:
        raise RuntimeError("Cannot arrange %d images - maximum is %d" % (n_inputs, max(arrangement_dict.keys())))
    return arrangement_dict[n_inputs]


def do_image_comparison_PIL(images, box, output, info=None):
    """Put together thsame crop region from all images into one big image, 
    together with text overlay for each image.

    Parameters
    ----------
    images : list[str]
        Input image filenames
    box : (float, float, float, float)
        Crop region (left, upper, right, lower)
    output : str
        Output filename
    info : list[str], optional
        List of fields to put on each image
    """
    crop_w = box[2]-box[0]
    crop_h = box[3]-box[1]
    regions = []
    # Get crop regions (with text) for each input image
    for im_filename in images:
        with PIL.Image.open(im_filename) as img:
            region = img.crop(box)

            # Add text
            if info:
                exif = {
                    PIL.ExifTags.TAGS[k]: v
                    for k, v in img._getexif().items()
                    if k in PIL.ExifTags.TAGS
                }
                # for k,v in exif.items():
                #     print(k, v, type(v))
                    # ExposureTime (1, 125)
                    # LensModel E PZ 16-50mm F3.5-5.6 OSS
                    # FNumber (160, 10)
                    # ISOSpeedRatings 100
                    # FocalLength (160, 10)

                # font size proportional to canvas size
                font = PIL.ImageFont.truetype("/Library/Fonts/GillSans.ttc", int(crop_h/22))
                draw = PIL.ImageDraw.Draw(region)

                # Actually add texts
                for i, this_info in enumerate(info):
                    text = ""
                    if this_info == "fstop":
                        fstop = exif_tuple_to_float(exif['FNumber'])
                        text = "F %.1f" % fstop
                    elif this_info == "focallength":
                        flength = exif_tuple_to_float(exif['FocalLength'])
                        text = "%d mm" % flength
                    elif this_info == "shutterspeed":
                        ss = exif['ExposureTime']
                        if ss[0] == 1:
                            text = "1/%d s" % ss[1]
                        else:
                            text = "%g s" % (ss[0]/ss[1])
                    elif this_info == "iso":
                        text = "ISO %d" % exif['ISOSpeedRatings']
                    elif this_info == "camera":
                        text = exif['Make'] + " " + exif['Model']
                    elif this_info == "lens":
                        text = exif['LensModel']
                    elif this_info == "datetime":
                        text = exif['DateTime']
                    elif this_info == "filename":
                        text = im_filename

                    # Make spacing, border size scale to canvas height
                    text_start_h = 10
                    text_space_h = font.size
                    text_x = 20
                    text_y = text_start_h+text_space_h*i
                    shadowcolor = 'black'
                    # thin border
                    border_size = max(int(font.size/20), 1)
                    draw.text((text_x-border_size, text_y), text, font=font, fill=shadowcolor)
                    draw.text((text_x+border_size, text_y), text, font=font, fill=shadowcolor)
                    draw.text((text_x, text_y-border_size), text, font=font, fill=shadowcolor)
                    draw.text((text_x, text_y+border_size), text, font=font, fill=shadowcolor)

                    # thicker border
                    draw.text((text_x-border_size, text_y-border_size), text, font=font, fill=shadowcolor)
                    draw.text((text_x+border_size, text_y-border_size), text, font=font, fill=shadowcolor)
                    draw.text((text_x-border_size, text_y+border_size), text, font=font, fill=shadowcolor)
                    draw.text((text_x+border_size, text_y+border_size), text, font=font, fill=shadowcolor)

                    # now draw the text over it
                    fillcolor = 'white'
                    draw.text((text_x, text_y), text, font=font, fill=fillcolor)

            regions.append(region)

    # Put all the images together into one big one
    n_row, n_col = determine_arrangement(len(images))
    new_w = n_col*crop_w
    new_h = n_row*crop_h
    out_img = PIL.Image.new('RGB', (new_w, new_h))
    for i, reg in enumerate(regions):
        row_ind = i // n_col
        col_ind = i % n_col
        loc = (col_ind*crop_w, row_ind*crop_h)  # upper left corner (left, height)
        out_img.paste(reg, loc)

    # Save to file
    out_img.save(output, quality=90)
    print("Saved to", output)


def do_image_comparison_wand(images, box, output, info):
    regions = []
    for im_filename in images:
        with Image(filename=im_filename) as img:
            pass
            # for k, v in img.metadata.items():
            #     print(k,v)
            #     'exif:ExposureTime'
            #     'exif:LensModel'
            #     'exif:FNumber'  # 56/10 = 5.6
            # img.crop(width=400, height=200, gravity='center')
            # print(img.size)

    n_row, n_col = determine_arrangement(len(images))
    crop_w = box[2]-box[0]
    crop_h = box[3]-box[1]
    new_w = 2*crop_w
    new_h = 2*crop_h


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",
                        help="Input images",
                        nargs="+")
    parser.add_argument("-output",
                        required=True,
                        help="Output file")
    parser.add_argument("-info",
                        nargs="*",
                        choices=["fstop", "focallength", "shutterspeed", "iso", "lens", "camera", "datetime", 'filename'],
                        help="info to put on each image")
    args = parser.parse_args()
    print(args)

    crop_h = 500
    crop_w = 1000
    start_h = 1500
    start_w = 2500

    # crop_h = 4000
    # crop_w = 6000
    # start_h = 0
    # start_w = 0

    # (left, upper, right, lower)
    box = (start_w, start_h, start_w+crop_w, start_h+crop_h)

    pil_output = os.path.splitext(args.output)[0]+"_pil.jpg"
    do_image_comparison_PIL(images=args.input, box=box, output=pil_output, info=args.info)

    wand_output = os.path.splitext(args.output)[0]+"_wand.jpg"
    # do_image_comparison_wand(images=args.input, box=box, output=wand_output, info=args.info)

