import numpy as np
import os
import sys
import ntpath
import time
from . import utils, html
from subprocess import Popen, PIPE


def save_images(webpage, visuals, image_path, aspect_ratio=1.0, width=512, use_wandb=False):
    """Save images to the disk.

    Parameters:
        webpage (the HTML class) -- the HTML webpage class that stores these imaegs (see html.py for more details)
        visuals (OrderedDict)    -- an ordered dictionary that stores (name, images (either tensor or numpy) ) pairs
        image_path (str)         -- the string is used to create image paths
        aspect_ratio (float)     -- the aspect ratio of saved images
        width (int)              -- the images will be resized to width x width

    This function will save images stored in 'visuals' to the HTML file specified by 'webpage'.
    """
    image_dir = webpage.get_image_dir()
    short_path = ntpath.basename(image_path[0])
    name = os.path.splitext(short_path)[0]

    webpage.add_header(name)
    ims, txts, links = [], [], []
    for label, im_data in visuals.items():
        im, mode = utils.tensor2im(im_data)
        image_name = '%s_%s.png' % (name, label)
        save_path = os.path.join(image_dir, image_name)
        utils.save_image(im, save_path, mode)
        ims.append(image_name)
        txts.append(label)
        links.append(image_name)


def display_test_results(results_dir, visuals, iter):
    """Display current results on visdom; save current results to an HTML file.

    Parameters:
        visuals (OrderedDict) - - dictionary of images to display or save
        epoch (int) - - the current epoch
        save_result (bool) - - if save the current results to an HTML file
    """
    # save images to the disk
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)
    for label, image in visuals.items():
        image_numpy, mode = utils.tensor2im(image)
        img_path = os.path.join(results_dir, 'iter%.3d_%s.png' % (iter, label))
        utils.save_image(image_numpy, img_path, mode=mode)


class Visualizer:
    """This class includes several functions that can display/save images and print/save logging information.

    It uses a Python library 'visdom' for display, and a Python library 'dominate' (wrapped in 'HTML') for creating HTML
    files with images.
    """

    def __init__(self, opt):
        """Initialize the Visualizer class

        Parameters:
            opt -- stores all the experiment flags; needs to be a subclass of BaseOptions
        Step 1: Cache the training/test options
        Step 2: connect to a visdom server
        Step 3: create an HTML object for saveing HTML filters
        Step 4: create a logging file to store training losses
        """
        self.opt = opt  # cache the option
        self.name = opt.name
        self.saved = False
        self.img_dir = os.path.join(opt.checkpoints_dir, opt.name, 'images')
        utils.mkdirs(self.img_dir)
        # create a logging file to store training losses
        self.log_name = os.path.join(opt.checkpoints_dir, opt.name, 'loss_log.txt')
        with open(self.log_name, "a") as log_file:
            now = time.strftime("%c")
            log_file.write('================ Training Loss (%s) ================\n' % now)

    def reset(self):
        """Reset the self.saved status"""
        self.saved = False

    def display_current_results(self, visuals, epoch, iter, save_result):
        """Display current results on visdom; save current results to an HTML file.

        Parameters:
            visuals (OrderedDict) - - dictionary of images to display or save
            epoch (int) - - the current epoch
            save_result (bool) - - if save the current results to an HTML file
        """
        if save_result or not self.saved:  # save images.
            self.saved = True
            # save images to the disk
            for label, image in visuals.items():
                image_numpy, mode = utils.tensor2im(image)
                img_path = os.path.join(self.img_dir, 'epoch%.3d_iter%.3d_%s.png' % (epoch, iter, label))
                utils.save_image(image_numpy, img_path, mode=mode)

    # losses: same format as |losses| of plot_current_losses
    def print_current_losses(self, epoch, iters, losses, t_comp, t_data):
        """print current losses on console; also save the losses to the disk

        Parameters:
            epoch (int) -- current epoch
            iters (int) -- current training iteration during this epoch (reset to 0 at the end of every epoch)
            losses (OrderedDict) -- training losses stored in the format of (name, float) pairs
            t_comp (float) -- computational time per data point (normalized by batch_size)
            t_data (float) -- data loading time per data point (normalized by batch_size)
        """
        message = '(epoch: %d, iters: %d, time: %.3f, data: %.3f) ' % (epoch, iters, t_comp, t_data)
        for k, v in losses.items():
            message += '%s: %.3f ' % (k, v)

        print(message)  # print the message
        with open(self.log_name, "a") as log_file:
            log_file.write('%s\n' % message)  # save the message
