from PIL import Image, ImageDraw
import os

def average_RGB(image):
    """ 
    Calculate the average Red, Green, Blue of a whole image
    Temporarily convert to RGB mode if image is not already RGB
    """
    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    pixel_count = width * height
    sumR = sumG = sumB = 0
    for x in range(width):
        for y in range(height):
            sumR = sumR + image.getpixel((x,y))[0]
            sumG = sumG + image.getpixel((x,y))[1]
            sumB = sumB + image.getpixel((x,y))[2]

    return (int(sumR / pixel_count), int(sumG / pixel_count), int(sumB / pixel_count))


def average_RGB_for_folder(image_folder_path):
    data_path = "./Data/" + os.path.basename(image_folder_path) + ".txt"
    averageRGB = open(data_path, "w")
    for image_file in os.listdir(image_folder_path):
        if image_file.endswith(".jpg"):
            sourceIm = Image.open(os.path.join(image_folder_path, image_file))
            RGBtuple = str(average_RGB(sourceIm))[1:-1] # Slicing to get rid of ()
            averageRGB.write(RGBtuple + "|" + image_file)
            averageRGB.write("\n")
            print(f"Wrote from {image_file}. Size {sourceIm.size}. RGB {RGBtuple}")
    averageRGB.close()


def fill_image(image, RGB_tuple):
    """Returns a one-color image, same dimension as original"""
    return Image.new('RGB', image.size, RGB_tuple)


def pixelate(image, step):
    """ Divide original image into smaller images, and
    fill small images with the average_RGB color, to create pixelate effect"""
    width, height = image.size
    temp = image.copy()

    for x in range(0, width, step):
        for y in range(0, height, step):
            # Crop into smaller image
            small_image = temp.crop((x, y, x + step, y + step))

            # Get a mono-color copy with color = average_RGB(small_image)
            one_color = fill_image(small_image, average_RGB(small_image))

            # Paste the mono-color copy onto the spot
            temp.paste(one_color, (x, y))
    
    temp.save("pixelated.jpg")
    return temp


def square_crop(image, destination_folder):
    """Crop images into square, with square side = min(width, height)"""
    width, height = image.size
    file_name = os.path.basename(image.filename)[0:-4] + "_cropped.jpg"
    file_path = os.path.join(destination_folder, file_name)
    if width > height:
        side = height
        x = int((width - height) / 2)
        image.crop((x, 0, x + side, side)).save(file_path)
    elif width < height:
        side = width
        x = int((height - width) / 2)
        image.crop((0, x, side, x + side)).save(file_path)
    else:
        image.save(file_path)
    print("Saved " + file_path)


def create_cropped_folder(source_images_folder):
    """ 
    Square cropping all source images in a folder, and save to different folder 
    """
    cropped_images_folder = "./SourceImages/" + os.path.basename(source_images_folder) + "-cropped"
    if not os.path.exists(cropped_images_folder):
        os.makedirs(cropped_images_folder)
        print("Created " + cropped_images_folder)
        for image_file in os.listdir(source_images_folder):
            if image_file.endswith(".jpg"):
                sourceIm = Image.open(source_images_folder + "/" + image_file)
                square_crop(sourceIm, cropped_images_folder)
    else:
        print(cropped_images_folder + " existed")
    
    return cropped_images_folder


def create_database(source_images_folder):
    """
    Crop all source images into squares, then
    create RGB data file for all cropped images
    """
    cropped_images_folder = create_cropped_folder(source_images_folder)
    data_path = "./Data/" + os.path.basename(cropped_images_folder) + ".txt"  
    
    if not(os.path.exists(data_path)):
        average_RGB_for_folder(cropped_images_folder)
    else:
        print(data_path + " existed")
    return data_path


def find_closest_image(input_RGBtuple, data_path):
    min_dist = 9999
    min_filename = ""
    R, G, B = input_RGBtuple
    with open(data_path) as RGB_data:
        for line in RGB_data:
            RGB_tuple, file_name = line.split("|")
            R_data, G_data, B_data = (int(x) for x in RGB_tuple.split(","))
            # Pythagoreans color distance
            color_dist = ((R - R_data)**2 +
                          (G - G_data)**2 +
                          (B - B_data)**2) ** 0.5
            if color_dist < min_dist:
                min_dist = color_dist
                min_filename = file_name.strip() # Remove "\n"
    
    # Return file path of the closest match
    return os.path.basename(data_path)[0:-4] + "/" + min_filename         


def create_photomosaics(inputIm, RGB_data_path, pixelation_step, sourceIm_size):
    width, height = inputIm.size
    expansion = int(sourceIm_size / pixelation_step)
    output = Image.new("RGB", (width * expansion, height * expansion))

    for x in range(0, width, pixelation_step):
        for y in range(0, height, pixelation_step):
            # Crop into smaller components square
            small_image = inputIm.crop((x, y, x + pixelation_step, y + pixelation_step))

            # Average RGB of component square
            aveRGB = average_RGB(small_image)

            # Find source image that match the component square's color
            source_image_path = find_closest_image(aveRGB, RGB_data_path)

            # Resize then paste the source image found onto output
            source_image = Image.open("./SourceImages/" + source_image_path)
            source_image_resized = source_image.resize((sourceIm_size, sourceIm_size))
            output.paste(source_image_resized, (x * expansion, y * expansion))
            print("Pasted " + source_image_path)

    if output.size[0] > 8000:
        output = output.resize((8000, 8000))
    
    output_path = ("./Output/" + 
                  os.path.basename(inputIm.filename)[0:-4] + 
                  "-mosaics-" +
                  os.path.basename(RGB_data_path)[0:-12] +
                  ".jpg")
    output.save(output_path)
            

if __name__ == "__main__":
    source_images = "./SourceImages/panda1000"
    inputIm = Image.open("input2.jpg")
    
    datapath = create_database(source_images)
    
    create_photomosaics(inputIm, datapath, 10, 100)