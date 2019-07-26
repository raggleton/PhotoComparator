# PhotoComparator

Script to produce a simple larger image composed of the same crop from various input images.
Useful to compare e.g. different lenses, apertures, ISOs.

## Requirements

- Python 2 or 3 (tested with 3.7)
- Pillow python library: `pip install Pillow`

(Or should I use `wand`)?

## Running

See `./makeComparison.py -h`:

```
./makeComparison.py <input1> <input2> ... -output <output filename> -info <info1> <info2> ...
```

where `<info1>` etc can be any from: 
    
- `fstop`
- `focallength`
- `shutterspeed`
- `iso`
- `lens`
- `camera`
- `datetime`
- `filename`

### Example

```
./makeComparison.py image1.jpg image2.jpg -output MyComparison -info fstop iso lens filename
```

To produce:

## Ideas

- Allow user to specify location & size of crop region
- Some way to auto-compare images with same fstop, or same focal length, etc