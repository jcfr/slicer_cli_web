import range from './range.jade';
import color from './color.jade';
import widget from './widget.jade';
import boolean from './boolean.jade';
import enumeration from './enumeration.jade';
import file from './file.jade';

export default {
    range,
    color,
    string: widget,
    number: widget,
    boolean,
    'string-vector': widget,
    'number-vector': widget,
    'string-enumeration': enumeration,
    'number-enumeration': enumeration,
    file,
    image: file,
    directory: file,
    'new-file': file
};
