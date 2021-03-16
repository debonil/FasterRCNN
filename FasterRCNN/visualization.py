from .dataset import VOC
from .models import region_proposal_network
from .models import intersection_over_union

import imageio
from PIL import Image, ImageDraw

def draw_rectangle(ctx, x_min, y_min, x_max, y_max, color, thickness = 4):
  ctx.rectangle(xy = [(x_min, y_min), (x_max, y_max)], outline = color, width = thickness)

def draw_filled_rectangle(ctx, x_min, y_min, x_max, y_max, color):
  ctx.rectangle(xy = [(x_min, y_min), (x_max, y_max)], fill = color)

def show_annotated_image(voc, filename, draw_anchor_points = True, draw_anchor_intersections = False, image_input_map = None, anchor_map = None):
  # Load image
  filepath = voc.get_full_path(filename = filename)
  info = voc.get_image_description(path = filepath)
  data = imageio.imread(filepath, pilmode = "RGB")
  image = Image.fromarray(data, mode = "RGB")
  boxes = info.get_boxes()

  # Because we loaded it ourselves, we are responsible for rescaling it
  image = image.resize((info.width, info.height), resample = Image.BILINEAR)

  # Draw ground truth boxes
  _draw_ground_truth_boxes(image = image, boxes = boxes)

  # Draw anchor boxes and intersection areas, if requested
  if draw_anchor_intersections or draw_anchor_points:
    _draw_anchor_box_intersections(image = image, ground_truth_boxes = boxes, draw_anchor_points = draw_anchor_points, input_image_shape = image_input_map.shape[1:])

  # Display image
  image.show()

def _draw_ground_truth_boxes(image, boxes):
  # Draw green boxes
  ctx = ImageDraw.Draw(image)
  for box in boxes:
    draw_rectangle(ctx, x_min = box.x_min, y_min = box.y_min, x_max = box.x_max, y_max = box.y_max, color = (0, 255, 0, 255))
    print("box=%s" % str(box))

def _draw_anchor_box_intersections(image, ground_truth_boxes, draw_anchor_points, input_image_shape):
  ctx = ImageDraw.Draw(image, mode = "RGBA")

  anchor_boxes, anchor_boxes_valid = region_proposal_network.compute_all_anchor_boxes(input_image_shape = input_image_shape)

  ground_truth_regressions, positive_anchors, negative_anchors = region_proposal_network.compute_anchor_label_assignments(ground_truth_object_boxes = ground_truth_boxes, anchor_boxes = anchor_boxes, anchor_boxes_valid = anchor_boxes_valid)

  for y in range(anchor_boxes.shape[0]):
    for x in range(anchor_boxes.shape[1]):
      anchors_per_location = int(anchor_boxes.shape[2] / 4)
      assert int(anchor_boxes.shape[2]) % int(4) == 0
      for anchor_num in range(anchors_per_location):
        # Extract box
        box = anchor_boxes[y, x, anchor_num * 4 : anchor_num * 4 + 4]
        center_y = box[0]
        center_x = box[1]
        height = box[2]
        width = box[3]
        anchor_y_min = center_y - 0.5 * height
        anchor_x_min = center_x - 0.5 * width
        anchor_y_max = center_y + 0.5 * height
        anchor_x_max = center_x + 0.5 * width

        # Draw anchor center pos
        if draw_anchor_points:
          size = 1
          any_positive = True in [ ground_truth_regressions[y,x,k,2] > 0 for k in range(ground_truth_regressions.shape[2]) ]
          color = (0, 255, 0, 255) if any_positive else (255, 0, 0, 255)
          draw_filled_rectangle(ctx, y_min = center_y - size, x_min = center_x - size, y_max = center_y + size, x_max = center_x + size, color = color)

        ## Does it intersect with any ground truth box?
        #for box in ground_truth_boxes:
        #  box1 = (anchor_y_min, anchor_x_min, anchor_y_max, anchor_x_max)
        #  box2 = (box.y_min, box.x_min, box.y_max, box.x_max)

        #  iou = intersection_over_union.intersection_over_union(box1 = box1, box2 = box2)
        #  if iou > 0.7:
        #    # Render intersection area
        #    intersection_box = intersection_over_union.intersection(box1 = box1, box2 = box2)
        #    draw_filled_rectangle(ctx, y_min = intersection_box[0], x_min = intersection_box[1], y_max = intersection_box[2], x_max = intersection_box[3], color = (255, 0, 0, 64))

        #    # Draw the anchor box outline
        #    draw_rectangle(ctx, x_min = anchor_x_min, y_min = anchor_y_min, x_max = anchor_x_max, y_max = anchor_y_max, color = (255, 0, 0, 255))

  # Draw all anchor boxes labeled as object in yellow
  for i in range(len(positive_anchors)):
    y = positive_anchors[i][0]
    x = positive_anchors[i][1]
    k = positive_anchors[i][2]

    # Extract box and draw
    box = anchor_boxes[y, x, k * 4 : k * 4 + 4]
    center_y = box[0]
    center_x = box[1]
    height = box[2]
    width = box[3]
    anchor_y_min = center_y - 0.5 * height
    anchor_x_min = center_x - 0.5 * width
    anchor_y_max = center_y + 0.5 * height
    anchor_x_max = center_x + 0.5 * width
    
    draw_rectangle(ctx, x_min = anchor_x_min, y_min = anchor_y_min, x_max = anchor_x_max, y_max = anchor_y_max, color = (255, 255, 0, 255))