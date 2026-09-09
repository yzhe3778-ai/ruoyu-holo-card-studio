"""Validate four equal-size image layers and genuine transparent alpha."""
from pathlib import Path
from PIL import Image,ImageStat,ImageChops,ImageFilter
import argparse,json

def validate(project):
    root=Path(project);report={};size=None
    for name in ['subject','background','lineart','text']:
        file=root/'assets'/(name+'.png')
        with Image.open(file) as im:
            if im.format!='PNG':raise ValueError(str(file)+' is not a PNG')
            if not size:size=im.size
            if im.size!=size:raise ValueError('Layer dimensions differ: '+name)
            if min(im.size)<256:raise ValueError('Artwork is too small')
            item={'size':im.size,'mode':im.mode}
            if name in ['subject','text']:
                if 'A' not in im.getbands():raise ValueError(name+' lacks real alpha; a painted checkerboard is invalid')
                alpha=im.getchannel('A');hist=alpha.histogram();transparent=sum(hist[:16])/sum(hist);solid=sum(hist[128:])/sum(hist)
                if transparent<.05 or solid<.001:raise ValueError(name+' needs both visible and truly transparent pixels (at least 5% transparent)')
                item.update(transparent_fraction=round(transparent,4),visible_fraction=round(solid,4))
                if name=='subject':
                    mask=alpha.point(lambda p:255 if p>=128 else 0)
                    box=mask.getbbox();item['bounds']=box
                    item['review_warnings']=[]
                    if box and (box[0]==0 or box[1]==0 or box[2]==im.width or box[3]==im.height):
                        item['review_warnings'].append('Subject touches canvas edge: inspect both tilted views for cut edges')
            if name=='lineart':
                lo,hi=im.convert('L').getextrema()
                if lo>80 or hi<230:raise ValueError('Line art needs dark contours on white')
                hist=im.convert('L').histogram()
                if sum(hist[230:])/sum(hist)<.5:raise ValueError('Line art must be sparse on a mostly white canvas')
                dark=im.convert('L').point(lambda p:255 if p<80 else 0)
                outside=ImageChops.multiply(dark,ImageChops.invert(mask.filter(ImageFilter.MaxFilter(15))))
                ratio=sum(outside.histogram()[128:])/max(1,sum(dark.histogram()[128:]))
                item['outside_subject_fraction']=round(ratio,4)
                item['review_warnings']=['Line art may drift outside subject; visually compare registration'] if ratio>.1 else []
            report[name]=item
    (root/'asset-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');a=p.parse_args();print(json.dumps(validate(a.project),indent=2))
